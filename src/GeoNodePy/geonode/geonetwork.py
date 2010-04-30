import urllib, urllib2, cookielib
from datetime import date
from django.template import Context
from django.template.loader import get_template
from xml.dom import minidom
from xml.etree.ElementTree import XML

class Catalog(object):

    def __init__(self, base, user, password):
        self.base = base
        self.user = user
        self.password = password
        self._group_ids = {}
        self._operation_ids = {}


    def login(self):
        url = "%ssrv/en/xml.user.login" % self.base
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        post = urllib.urlencode({
            "username": self.user,
            "password": self.password
        })
        request = urllib2.Request(url, post, headers)
        response = urllib2.urlopen(request)
        body = response.read()
        dom = minidom.parseString(body)
        assert dom.childNodes[0].nodeName == 'ok', "GeoNetwork login failed!"

        self.cookies = cookielib.CookieJar()
        self.cookies.extract_cookies(response, request)
        cookie_handler = urllib2.HTTPCookieProcessor(self.cookies)
        redirect_handler = urllib2.HTTPRedirectHandler()
        self.opener = urllib2.build_opener(redirect_handler, cookie_handler)

    def logout(self):
        url = "%ssrv/en/xml.user.logout" % self.base
        request = urllib2.Request(url)
        response = self.opener.open(request)

    def get_by_uuid(self, uuid):
        pass

    def create_from_layer(self, layer):
        tpl = get_template("maps/csw/transaction_insert.xml")
        now = date.today()
        ctx = Context({
            'layer': layer,
            'now': now,
            'uuid': layer.uuid
        })
        md_doc = tpl.render(ctx)

        url = "%ssrv/en/csw" % self.base
        headers = {
            "Content-Type": "application/xml",
            "Accept": "text/plain"
        }
        request = urllib2.Request(url, md_doc, headers)
        response = self.urlopen(request)

        # print layer.uuid
        # print response.read()
        # TODO: Parse response, check for error report


        # Turn on the "view" permission (aka publish) for
        # the "all" group in GeoNetwork so that the layer
        # will be searchable via CSW without admin login.
        # all other privileges are set to False for all 
        # groups.
        self.set_metadata_privs(layer.uuid, {"all":  {"view": True}})
        
        return self.base + "srv/en/csw?" + urllib.urlencode({
            "request": "GetRecordById",
            "service": "CSW",
            "version": "2.0.2",
            "OutputSchema": "http://www.isotc211.org/2005/gmd",
            "ElementSetName": "full",
            "id": layer.uuid
        })

    def update_from_layer(self, record, layer):
        pass

    def set_metadata_privs(self, uuid, privileges):
        """
        set the full set of geonetwork privileges on the item with the 
        specified uuid based on the dictionary given of the form: 
        {
          'group_name1': {'operation1': True, 'operation2': True, ...},
          'group_name2': ...
        }

        all unspecified operations and operations for unspecified groups 
        are set to False.
        """
        
        # XXX This is a fairly ugly workaround that makes 
        # requests similar to those made by the GeoNetwork
        # admin based on the recommendation here: 
        # http://bit.ly/ccVEU7

        
        get_dbid_url = self.base + 'srv/en/portal.search.present?' + urllib.urlencode({'uuid': uuid})

        # get the id of the data.
        request = urllib2.Request(get_dbid_url)
        response = self.urlopen(request)
        doc = XML(response.read())
        data_dbid = doc.find('metadata/{http://www.fao.org/geonetwork}info/id').text

        # update group and operation info if needed
        if len(self._group_ids) == 0:
            self._group_ids = self._get_group_ids()
        if len(self._operation_ids) == 0:
            self._operation_ids = self._get_operation_ids()

        # build params that represent the privilege configuration
        priv_params = {
            "id": data_dbid, # "uuid": layer.uuid, # you can say this instead in newer versions of GN 
        }
        for group, privs in privileges.items():
            group_id = self._group_ids[group.lower()]
            for op, state in privs.items():
                if state != True:
                    continue
                op_id = self._operation_ids[op.lower()]
                priv_params['_%s_%s' % (group_id, op_id)] = 'on'

        # update all privileges
        update_privs_url = self.base + "srv/en/metadata.admin?" + urllib.urlencode(priv_params)
        request = urllib2.Request(update_privs_url)
        response = self.urlopen(request)

        # TODO: check for error report  
        
    def _get_group_ids(self):
        """
        helper to fetch the set of geonetwork 
        groups.
        """
        # get the ids of the groups.
        get_groups_url = self.base + "srv/en/xml.info?" + urllib.urlencode({'type': 'groups'})
        request = urllib2.Request(get_groups_url)
        response = self.urlopen(request)
        doc = XML(response.read())
        groups = {}
        for gp in doc.findall('groups/group'):
            groups[gp.find('name').text.lower()] = gp.attrib['id']
        return groups

    def _get_operation_ids(self):
        """
        helper to fetch the set of geonetwork 
        'operations' (privileges)
        """
        # get the ids of the operations    
        get_ops_url = self.base + "srv/en/xml.info?" + urllib.urlencode({'type': 'operations'})
        request = urllib2.Request(get_ops_url)
        response = self.urlopen(request)
        doc = XML(response.read())
        ops = {}
        for op in doc.findall('operations/operation'):
            ops[op.find('name').text.lower()] = op.attrib['id']
        return ops

    def urlopen(self, request):
        if self.opener is None:
            return urllib2.urlopen(request)
        else:
            return self.opener.open(request)