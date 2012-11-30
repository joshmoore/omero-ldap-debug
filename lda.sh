#!/bin/bash

(

set -e
set -u


export CLASSPATH=.:`echo lib/server/*.jar | sed 's/ /:/g'`
cat > ldap.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN" "http://www.springframework.org/dtd/spring-beans.dtd">
<beans>

   <bean id="ldapConfig" class="ome.security.auth.LdapConfig">
      <constructor-arg index="0" value="true"/>
      <constructor-arg index="1" value="default"/>
      <constructor-arg index="2" value="(objectClass=person)"/>
      <constructor-arg index="3" value="(objectClass=group)"/>
      <constructor-arg index="4" value="omeName=cn,firstName=givenName,lastName=sn,email=mail"/>
      <constructor-arg index="5" value="name=cn"/>
    </bean>

    <bean id="defaultContextSource"
        class="org.springframework.security.ldap.DefaultSpringSecurityContextSource">
        <constructor-arg value="ldaps://bioch-ad3.bioch.ox.ac.uk:636"/>
        <property name="userDn" value="cn=omerolookup,ou=Service Accounts,dc=bioch,dc=ox,dc=ac,dc=uk"/>
        <property name="password" value="$1"/>
        <property name="base" value="dc=bioch,dc=ox,dc=ac,dc=uk"/>
        <property name="dirObjectFactory"
            value="org.springframework.ldap.core.support.DefaultDirObjectFactory" />
    </bean>

    <bean id="keystore" class="ome.security.KeyAndTrustStoreConfiguration" lazy-init="false">
      <description>Sets the keystore and truststore System properties on start-up</description>
      <property name="keyStore" value="/home/dpwrussell/keys/keystore-empty.jks"/>
      <property name="keyStorePassword" value="changeit"/>
      <property name="trustStore" value="/home/dpwrussell/keys/keystore.jks"/>
      <property name="trustStorePassword" value="changeit"/>
    </bean>

    <bean id="ldapTemplate" class="org.springframework.ldap.core.LdapTemplate">
        <constructor-arg ref="defaultContextSource" />
    </bean>

</beans>
EOF

cat > ldap.java <<EOF
/*
 *   Copyright 2011 Glencoe Software, Inc. All rights reserved.
 *   Use is subject to license terms supplied in LICENSE.txt
 */

import java.util.Arrays;
import java.util.List;

import javax.naming.NamingException;
import javax.naming.directory.SearchControls;

import ome.security.auth.LdapConfig;

import org.springframework.context.support.FileSystemXmlApplicationContext;
import org.springframework.ldap.core.*;
import org.springframework.ldap.core.support.*;

public class ldap {

    public static void main(String[] args) throws Exception {

        // Configuration (from XML above)
        FileSystemXmlApplicationContext ctx =
                new FileSystemXmlApplicationContext(new String[]{"classpath:ldap.xml"});

        // Objects we need to use.
        LdapConfig config = ctx.getBean(LdapConfig.class);
        LdapTemplate template = ctx.getBean(LdapTemplate.class);

        String USER = "omerotest";
        System.out.println("Looking for user: " + USER);
        List<String> results = (List<String>)
        template.search("", config.usernameFilter(USER).encode(),
            new ContextMapper(){
                public Object mapFromContext(Object arg0) {
                    DirContextAdapter ctx = (DirContextAdapter) arg0;
                    System.out.println(ctx.getNameInNamespace());
                    return ctx.getNameInNamespace();
                }});
        if (results == null || results.size() == 0) {
            System.out.println("Nothing found!");
        }
    }
}
EOF

cat > ldap.properties <<EOF
log4j.rootCategory=trace, stderr
log4j.appender.stderr=org.apache.log4j.ConsoleAppender
log4j.appender.stderr.target=System.err
log4j.appender.stderr.layout=org.apache.log4j.PatternLayout
log4j.appender.stderr.layout.ConversionPattern = %d %-10.10r [%10.10t] %-6.6p %40.40c %x - %m\n

log4j.category.example = info
EOF

javac ldap.java
java -Dlog4j.configuration=ldap.properties ldap "$@"

)

rm -f ldap.java
rm -f ldap*.class
rm -f ldap.properties
rm -f ldap.xml
