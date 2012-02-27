#!/bin/bash

# Location of the expanded GeoNode tarball
INSTALL_DIR=.
# Location of the target filesystem, it may be blank
# or something like $(CURDIR)/debian/geonode/
TARGET_ROOT=''
# Tomcat webapps directory
TOMCAT_WEBAPPS="${TARGET_ROOT}/var/lib/tomcat5/webapps"
TOMCAT_LOGS="${TARGET_ROOT}/var/log/tomcat5/"
TOMCAT_DEFAULTS="/etc/tomcat5/tomcat5.conf"
TOMCAT_USER=tomcat
# Geoserver data dir, it will survive removals and upgrades
GEOSERVER_DATA_DIR="${TARGET_ROOT}/var/lib/geoserver/geonode-data"
# Place where GeoNode media is going to be served
GEONODE_WWW="${TARGET_ROOT}/var/www/geonode"
# Apache sites directory
APACHE_CONFIG_FILE="${TARGET_ROOT}/etc/httpd/conf.d/geonode.conf"
# Place where the GeoNode virtualenv would be installed
GEONODE_LIB="${TARGET_ROOT}/var/lib/geonode"
# Path to preferred location of binaries (might be /usr/sbin for CentOS)
GEONODE_BIN="${TARGET_ROOT}/usr/local/bin/"
# Path to place miscelaneous patches and scripts used during the install
GEONODE_SHARE="${TARGET_ROOT}/usr/share/geonode"
# Path to GeoNode configuration and customization
GEONODE_ETC="${TARGET_ROOT}/etc/geonode"
# Path to GeoNode logging folder
GEONODE_LOG="${TARGET_ROOT}/var/log/geonode"

POSTGRES_SYSTEM_USER="postgres"
GEONODE_DATABASE="geonode"
GEONODE_DATABASE_USER="geonode"
GEONODE_DATABASE_PASSWORD="abc123"

CUSTOM_TEMPLATE_DIR="${GEONODE_ETC}/templates"
CUSTOM_MEDIA_DIR="${GEONODE_ETC}/media"

# OS preferred way of starting or stopping services
# for example 'service httpd' or '/etc/init.d/apache2'
APACHE_SERVICE="service httpd"
APACHE_SERVICE="true"
# sama sama
TOMCAT_SERVICE="true"

WEB_CONTENT_USER="apache"

function configure_apache() {
  true # in centos, no extra steps are needed - just putting the files in the right place is enough
}

function setup_postgres_once() {
su - "${POSTGRES_SYSTEM_USER}" <<EOF
createdb -E UTF8 "${GEONODE_DATABASE}"
createlang -d "${GEONODE_DATABASE}" plpgsql
psql -d "${GEONODE_DATABASE}" -f /usr/share/pgsql/contrib/postgis.sql
psql -d "${GEONODE_DATABASE}" -f /usr/share/pgsql/contrib/spatial_ref_sys.sql
EOF

su - postgres -c psql << EOF
CREATE ROLE ${GEONODE_DATABASE_USER} WITH LOGIN PASSWORD '${GEONODE_DATABASE_PASSWORD}' SUPERUSER INHERIT;
EOF
}
