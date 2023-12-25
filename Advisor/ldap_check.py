import ldap3

AD_SERVER = '10.10.1.2'
# AD_USERNAME = '230815'
# AD_PASSWORD = '8qVh27_!HGca'
# AD_USERNAME = 'o.shevchenko'
# AD_PASSWORD = 'vuB504'
def check_ad_credentials(ad_server, username, password):
    try:
        with ldap3.Connection(ad_server, user=username, password=password) as conn:
            if not conn.bind():
                return False
            
            username = username.split('@')[0]

            base_dn = 'OU=UsersDoc,DC=iab,DC=kz'
            search_filter = f'(&(objectClass=user)(sAMAccountName={username}))'

            conn.search(base_dn, search_filter, attributes=['memberOf'])
            
            if len(conn.entries) != 1:
                return False

            member_of = conn.entries[0]['memberOf'].value if 'memberOf' in conn.entries[0] else None
            
            if member_of is None:
                return False

            for group in member_of:
                if 'CN=Эдвайзинг центр,' in group:
                    return True

            return False
    except ldap3.core.exceptions.LDAPException as e:
            print(f"Ошибка LDAP: {e}")
            return False