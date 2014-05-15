Usage instructions:
-------------------

 * Clone this repository to some near your OMERO installation

 * Edit ldap_debug.py with your configuration properties. For example,

```
~/OMERO-CURRENT$ bin/omero config get | grep ldap
omero.ldap.base=ou=lifesci,o=dundee
omero.ldap.config=true
omero.ldap.urls=ldap://ldap.lifesci.dundee.ac.uk:389
```

 * cd to your OMERO installation directory

 * run `python omero-ldap-debug/ldap_debug.py username`. Output will look something like:

```
omero@gretzky:~/OMERO-CURRENT$ python omero-ldap-debug/ldap_debug.py jamoore
Note: ldap.java uses unchecked or unsafe operations.
Note: Recompile with -Xlint:unchecked for details.
22:05:59.324 [main] INFO  o.s.c.s.FileSystemXmlApplicationContext - Refreshing org.springframework.context.support.FileSystemXmlApplicationContext@21f3aa07: startup date [Thu May 15 22:05:59 BST 2014]; root of context hierarchy
22:05:59.373 [main] INFO  o.s.b.f.xml.XmlBeanDefinitionReader - Loading XML bean definitions from class path resource [ldap.xml]
22:05:59.573 [main] INFO  o.s.b.f.s.DefaultListableBeanFactory - Pre-instantiating singletons in org.springframework.beans.factory.support.DefaultListableBeanFactory@335856a5: defining beans [ldapConfig,defaultContextSource,ldapTemplate]; root of factory hierarchy
22:05:59.639 [main] INFO  o.s.s.l.DefaultSpringSecurityContextSource -  URL 'ldap://ldap.lifesci.dundee.ac.uk:389', root DN is ''
22:05:59.672 [main] INFO  o.s.l.c.s.AbstractContextSource - Property 'userDn' not set - anonymous context will be used for read-write operations
Looking for user: jamoore
cn=jamoore,ou=edir,ou=people,ou=lifesci,o=dundee
Groups:[]
```
