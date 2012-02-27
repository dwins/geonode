service postgresql initdb
sed '72s!ident!md5!' -i /var/lib/pgsql/data/pg_hba.conf
service postgresql start
