import ldap

def ldap_connect(username, password):
    try:
        conn = ldap.initialize("ldap://10.10.1.2:389")
        conn.simple_bind_s(username, password)
        
        search_base = "dc=iab,dc=kz"
        search_filter = f"(sAMAccountName={username.split('@')[0]})"
        
        results = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
        
        if results:
            # Пользователь найден, можно получить дополнительные атрибуты
            # например, results[0][1]['givenName'][0] и так далее
            return True, "Дополнительная информация..."
        else:
            return False, "Пользователь не найден"
    except ldap.LDAPError as e:
        return False, str(e)