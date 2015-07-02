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
    <constructor-arg index="1" value=":query:(memberUid=@{cn})"/>
    <constructor-arg index="2" value="(objectClass=person)"/>
    <constructor-arg index="3" value="(objectClass=posixgroup)"/>
    <constructor-arg index="4" value="omeName=cn,firstName=givenName,lastName=sn,email=mail"/>
    <constructor-arg index="5" value="name=cn"/>
    </bean>

    <bean id="defaultContextSource"
        class="org.springframework.security.ldap.DefaultSpringSecurityContextSource">
        <constructor-arg value="ldap://ldap.lifesci.dundee.ac.uk:389"/>
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

    <bean name="ldap" class="MockLdapImpl">
        <constructor-arg ref="defaultContextSource"/>
        <constructor-arg ref="ldapTemplate"/>
        <constructor-arg><bean class="ome.system.Roles"/></constructor-arg>
        <constructor-arg ref="ldapConfig" />
        <constructor-arg><bean class="MockRoleProvider"/></constructor-arg>
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

import ome.conditions.ApiUsageException;

import ome.logic.LdapImpl;

import ome.model.meta.Experimenter;
import ome.model.meta.ExperimenterGroup;
import ome.model.internal.Permissions;

import ome.security.auth.AttributeSet;
import ome.security.auth.GroupAttributeMapper;
import ome.security.auth.PersonContextMapper;
import ome.security.auth.RoleProvider;
import ome.security.auth.QueryNewUserGroupBean;
import ome.security.auth.LdapConfig;

import ome.system.OmeroContext;
import ome.system.Roles;

import org.springframework.ldap.core.*;
import org.springframework.ldap.core.support.*;
import org.springframework.ldap.filter.Filter;

import ch.qos.logback.classic.Level;

@SuppressWarnings("unchecked")
class MockLdapImpl extends LdapImpl {

    ContextSource ctx;
    LdapConfig config;
    LdapOperations ldap;
    RoleProvider provider;
    public MockLdapImpl(ContextSource ctx, LdapOperations ldap, Roles roles,
            LdapConfig config, RoleProvider roleProvider) {
        super(ctx, ldap, roles, config, roleProvider, null);
        this.ctx = ctx;
        this.ldap = ldap;
        this.config = config;
        this.provider = roleProvider;
    }

    public AttributeSet getAttributeSet(String username, String data) {
        // Copied, since all private

        // getBase
        String base = null;
        try {
            base = ctx.getReadOnlyContext().getNameInNamespace();
        } catch (NamingException e) {
            throw new ApiUsageException(
                    "Cannot get BASE from ContextSource. Naming exception! "
                            + e.toString());
        }

        // getPersonContextMapper
        PersonContextMapper mapper = new PersonContextMapper(config, base);

        // mapUserName
        Filter filter = config.usernameFilter(username);
        List<Experimenter> p = ldap.search("", filter.encode(),
                mapper.getControls(), mapper);

        Experimenter exp = null;
        if (p.size() == 1 && p.get(0) != null) {
            Experimenter e = p.get(0);
            if (provider.isIgnoreCaseLookup()) {
                if (e.getOmeName().equalsIgnoreCase(username)) {
                    exp = p.get(0);
                }
            } else {
                if (e.getOmeName().equals(username)) {
                    exp = p.get(0);
                }
            }
        }
        if (exp == null) {
            throw new ApiUsageException(
                "Cannot find unique user DistinguishedName: found=" + p.size());
        }

        // getAttributeSet
        String dn = mapper.getDn(exp);
        AttributeSet attrSet = mapper.getAttributeSet(exp);
        attrSet.put("dn", dn); // For queries
        return attrSet;
    }

}

class MockRoleProvider implements ome.security.auth.RoleProvider {

    public String nameById(long id) {
        return null;
    }

    public long createGroup(ExperimenterGroup group) {
        return -1;
    }

    public long createGroup(String name, Permissions perms, boolean strict){
        return -1;
    }

    public long createGroup(String name, Permissions perms, boolean strict,
            boolean isLdap) {
        System.out.println("Group: " + name);
        return -1;
    }

    public long createExperimenter(Experimenter experimenter,
            ExperimenterGroup defaultGroup, ExperimenterGroup... otherGroups) {
        return -1;
    }

    public void setDefaultGroup(final Experimenter user, final ExperimenterGroup group) {
    }

    public void setGroupOwner(final Experimenter user, final ExperimenterGroup group,
            final boolean value) {
    }

    public void addGroups(final Experimenter user, final ExperimenterGroup... groups) {
    }

    public void removeGroups(final Experimenter user,
            final ExperimenterGroup... groups) {
    }

    public boolean isIgnoreCaseLookup() {
        return false;
    }

}

@SuppressWarnings("unchecked")
public class ldap {

    static ch.qos.logback.classic.Logger root = (ch.qos.logback.classic.Logger)
        org.slf4j.LoggerFactory.getLogger(ch.qos.logback.classic.Logger.ROOT_LOGGER_NAME);

    public static void main(String[] args) throws Exception {

        root.setLevel(Level.WARN);

        // Configuration (from XML above)
        OmeroContext ctx = new OmeroContext(new String[]{"classpath:ldap.xml"});

        // Objects we need to use.
        MockLdapImpl ldap = ctx.getBean(MockLdapImpl.class);
        LdapConfig config = ctx.getBean(LdapConfig.class);
        LdapTemplate template = ctx.getBean(LdapTemplate.class);
        String query = config.getNewUserGroup().substring(7);

        for (final String arg : args) {
            System.out.println("Looking for user: " + arg);
            List<String> results = (List<String>)
            template.search("", config.usernameFilter(arg).encode(),
                new ContextMapper(){
                    public Object mapFromContext(Object arg0) {
                        DirContextAdapter ctx = (DirContextAdapter) arg0;
                        String dn = ctx.getNameInNamespace();
                        System.out.println("dn=" + dn);
                        System.out.println("groupSpec=" + query);
                        QueryNewUserGroupBean bean = new QueryNewUserGroupBean(query);
                        AttributeSet attr = ldap.getAttributeSet(arg, query);
                        bean.groups(arg, config, template, new MockRoleProvider(), attr);
                        return ctx.getNameInNamespace();
                    }});
            if (results == null || results.size() == 0) {
                System.out.println("Nothing found!");
            }
        }

        //String grpFilter = config.getGroupFilter().encode();
        //GroupAttributeMapper mapper = new GroupAttributeMapper(config);
        //List<String> filteredNames = (List<String>) template.search("", grpFilter, mapper);
        //System.out.println("Groups:" + filteredNames);
    }
}""")

def run(args):
    call("javac", "-Xlint:unchecked", "-cp", CLASSPATH, "ldap.java")
    call(*tuple(["java", "-cp", CLASSPATH,
                 "ldap"] + args))

def clean_files():
    for x in ("ldap.java", "ldap.xml"):
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
