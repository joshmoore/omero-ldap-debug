#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2014 Glencoe Software, Inc. All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Script to test an OMERO LDAP Connection by
writing a Java class and compiling it.
"""


import os
import sys
import glob
import subprocess

def call(*args):
    if subprocess.call(list(args)):
        raise Exception(" ".join(args))


dir = os.environ.get("OMERO_HOME", ".")
dir = os.path.abspath(dir)
dir = os.path.join(dir, "lib", "server")
jars = os.path.join(dir, "*.jar")
CLASSPATH = ["."]
CLASSPATH += glob.glob(jars)
if len(CLASSPATH) == 1:
    raise Exception("No jars found. Set OMERO_HOME or cd to OMERO")
CLASSPATH = os.path.pathsep.join(CLASSPATH)


def write_files():
    with open("ldap.xml", "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN" "http://www.springframework.org/dtd/spring-beans.dtd">
<beans>

<bean id="ldapConfig" class="ome.security.auth.LdapConfig">
    <constructor-arg index="0" value="true"/>
    <constructor-arg index="1" value=":attribute:memberOf"/>
    <constructor-arg index="2" value="(objectClass=person)"/>
    <constructor-arg index="3" value="(&amp;(objectClass=group)(mail=omero.flag))"/>
    <constructor-arg index="4" value="omeName=cn,firstName=givenName,lastName=sn,email=mail"/>
    <constructor-arg index="5" value="name=cn"/>
    </bean>

    <bean id="defaultContextSource"
        class="org.springframework.security.ldap.DefaultSpringSecurityContextSource">
        <constructor-arg value="ldaps://localhost:369"/>
        <property name="userDn" value="jamoore"/>
        <property name="password" value="$1"/>
        <property name="base" value="ou=lifesci,o=dundee"/>
        <property name="dirObjectFactory"
            value="org.springframework.ldap.core.support.DefaultDirObjectFactory" />
        <!-- http://forum.springsource.org/showthread.php?58963-Setting-java-naming-referral-using-namespace-configuration -->
        <property name="baseEnvironmentProperties">
            <map>
                <entry key="java.naming.referral">
                    <value>follow</value>
                </entry>
            </map>
        </property>
    </bean>

    <bean id="ldapTemplate" class="org.springframework.ldap.core.LdapTemplate">
        <constructor-arg ref="defaultContextSource" />
    </bean>

</beans>""")

    with open("ldap.java", "w") as f:
        f.write("""/*
*   Copyright 2011 Glencoe Software, Inc. All rights reserved.
*   Use is subject to license terms supplied in LICENSE.txt
*/

import java.util.Arrays;
import java.util.List;

import javax.naming.NamingException;
import javax.naming.directory.SearchControls;

import ome.security.auth.GroupAttributeMapper;
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

        String grpFilter = config.getGroupFilter().encode();
        GroupAttributeMapper mapper = new GroupAttributeMapper(config);
        List<String> filteredNames = (List<String>) template.search("", grpFilter, mapper);
        System.out.println("Groups:" + filteredNames);
    }
}""")

    with open("ldap.properties", "w") as f:
        f.write("""
log4j.rootCategory=trace, stderr
log4j.appender.stderr=org.apache.log4j.ConsoleAppender
log4j.appender.stderr.target=System.err
log4j.appender.stderr.layout=org.apache.log4j.PatternLayout
log4j.appender.stderr.layout.ConversionPattern = %d %-10.10r [%10.10t] %-6.6p %40.40c %x - %m\n

log4j.category.example = info
    """)

def run(args):
    call("javac", "-cp", CLASSPATH, "ldap.java")
    call(*tuple(["java", "-cp", CLASSPATH,
                 "-Dlog4j.configuration=ldap.properties", "ldap"] + args))

def clean_files():
    for x in ("ldap.java", "ldap.properties", "ldap.xml"):
        if os.path.exists(x):
            os.remove(x)

    for x in glob.glob("ldap*.class"):
        os.remove(x)

if __name__ == "__main__":
    try:
        write_files()
        run(sys.argv[1:])
    finally:
        clean_files()

