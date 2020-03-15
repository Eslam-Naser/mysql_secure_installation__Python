import MySQLdb as mysql


def check_mysql_connection(host, user, password=''):
    """
    A function used to check the ability to login to MySQL/Mariadb
    :param host: ie. 'localhost'  - :type String
    :param user: mysql user ie. 'root' - :type String
    :param password: mysql user's password - :type String
    :return: True||False
    """
    try:
        mysql.connect(host=host, user=user, passwd=password)
        return True
    except  mysql.Error:
        return False

def mysql_secure_installation(login_password, new_password, user='root',login_host='localhost', hosts=['hostname'], change_root_password= True, remove_anonymous_user= True, disallow_root_login_remotely= False, remove_test_db= True):
    """
    A function to perform the steps of mysql_secure_installation script
    :param login_password: Root's password to login to MySQL
    :param new_password: New desired Root password :type String
    :param user: MySQL user - default: 'root' :type String
    :param login_host: host to connect to - default: 'localhost' :type String
    :param hosts: List of hosts for the provided user i.e ['localhost', '127.0.0.1', '::1'] :type List
    :param change_root_password:  default: True - :type Boolean
    :param remove_anonymous_user: default: True - :type: Boolean
    :param disallow_root_login_remotely: default: False - :type Boolean
    :param remove_test_db: default: True - :type: Boolean
    :return:
    """
    if isinstance(hosts, str):
        hosts = hosts.split(',')
    info = {'change_root_pwd': None, 'hosts_failed': [], 'hosts_success': [],'remove_anonymous_user': None, 'remove_test_db': None, 'disallow_root_remotely': None }

    def remove_anon_user(cursor):
        if remove_anonymous_user:
            cursor.execute("select user, host from mysql.user where user='';")
            anon_user = cursor.fetchall()
            if len(anon_user) >= 1:
                cursor.execute('use mysql;')
                cursor.execute("DELETE FROM user WHERE user='';")
                cursor.execute("update mysql.user set plugin=null where user='root';")
                cursor.execute("select user, host from mysql.user where user='';")
                check = cursor.fetchall()
                if len(check) >= 1:
                    info['remove_anonymous_user'] = 1
                else:
                    info['remove_anonymous_user'] = 0
            else:
                info['remove_anonymous_user'] = 0

    def remove_testdb(cursor):
        def search_tuple(tups, elem):
            return filter(lambda tup: elem in tup, tups)
        if remove_test_db:
            cursor.execute("show databases;")
            testdb = cursor.fetchall()
            if search_tuple(testdb, 'test'):
                cursor.execute("drop database test;")
                info['remove_test_db'] = 0
            else:
                info['remove_test_db'] = 0

    def disallow_root_remotely(cursor):
        if disallow_root_login_remotely:
            cursor.execute("select user, host from mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');")
            remote = cursor.fetchall()
            if len(remote) >= 1:
                cursor.execute("DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');")
                cursor.execute("flush privileges;")
                info['disallow_root_remotely'] = 0
            else:
                info['disallow_root_remotely'] = 0

    if check_mysql_connection(host=login_host, user=user, password=login_password):
        try:
            connection = mysql.connect(host=login_host, user=user, passwd=login_password, db='mysql')
            cursor = connection.cursor()
            remove_anon_user(cursor)
            remove_testdb(cursor)
            disallow_root_remotely(cursor)
            if change_root_password:
                pwd = {}
                for host in hosts:
                    cursor.execute('use mysql;')
                    cursor.execute(
                        'update user set password=PASSWORD("{}") where User="{}" AND Host="{}";'.format(new_password,
                                                                                                        user, host))
                    cursor.execute('flush privileges;')
                    cursor.execute('select user, host, password from mysql.user where user="{}";'.format(user))
                    data = cursor.fetchall()
                    for d in data:
                        if d[1] == host:
                            pwd['{}'.format(d[1])] = d[2]

                out = set(hosts).symmetric_difference(set(pwd.keys()))
                info['hosts_failed'] = list(out)
                hosts_ = list(set(hosts) - set(list(out)))

                for host in hosts_:
                    if pwd[host] == pwd[login_host]:
                        info['hosts_success'].append(host)
                    else:
                        info['hosts_failed'].append(login_host)

                #if len(info['hosts_success']) >= 1:
                    #info['stdout'] = 'Password for user: {} @ Hosts: {} changed to the desired state'.format(user, info['hosts_success'])
                if len(info['hosts_failed']) >= 1:
                    info['change_root_pwd'] = 1
                #    info['stderr'] = 'Could NOT change password for User: {} @ Hosts: {}'.format(user,info['hosts_failed'])
                else:
                    info['change_root_pwd'] = 0
            connection.close()
        except mysql.Error as e:
            info['change_root_pwd'] = 1
            info['stderr'] = e

    elif check_mysql_connection(host=login_host, user=user, password=new_password):
        connection = mysql.connect(host=login_host, user=user, passwd=new_password, db='mysql')
        cursor_ = connection.cursor()
        remove_anon_user(cursor_)
        remove_testdb(cursor_)
        disallow_root_remotely(cursor_)
        info['change_root_pwd'] = 0
        info['stdout'] = 'Password of {}@{} Already meets the desired state'.format(user, login_host)

    else:
        info['change_root_pwd'] = 1
        info['stdout'] = 'Neither the provided old password nor the new password are correct'
    return info


### Example of Usage ###

# print(mysql_secure_installation(disallow_root_login_remotely=True, login_password='', new_password='password', hosts=['localhost', '::1', '127.0.0.1', 'controller.linux.com', 'controller', 'test']))
