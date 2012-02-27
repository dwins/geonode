setenforce 0
sed '19i-A RH-Firewall-1-INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT' -i /etc/sysconfig/iptables
service iptables restart
