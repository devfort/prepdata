#!/usr/bin/env python
#
# fetch (c) James Aylett 2009
#
# Given a sources.where (defaults to in the current directory), fetch
# everything in every section. More sophistication may arrive later, but probably
# after we start doing magic screen scraping options.
#
# module=<> changes behaviour from straight download (currently for VCS)

import ConfigParser
import optparse
import os
import subprocess

failed = {}

def value_to_url_github(value, name):
	bits = value.split('/')
	user = bits[0]
	if len(bits)>1:
	    project = bits[1]
	else:
	    project = name
	giturl = 'git://github.com/%s/%s.git' % (user, project,)
	return giturl

def process_git(cp, sect, directory):
	process_gits(cp, sect, directory, lambda x, y: x)

def process_github(cp, sect, directory):
	process_gits(cp, sect, directory, value_to_url_github)

def process_gits(cp, sect, directory, value_to_url):
	process_vcs(cp, sect, directory, value_to_url, ['git', 'clone'])
	
def process_subversion(cp, sect, directory):
	process_vcs(cp, sect, directory, lambda x, y: x, ['svn', 'co'])
	
def process_vcs(cp, sect, directory, value_to_url, checkout_cmd):
    for (name, value) in cp.items(sect):
        if name=='module' or name=='homepage':
            continue
        outdir = os.path.join(directory, name)
        if os.path.exists(outdir):
            if not os.path.isdir(outdir):
                errmsg = "Could not process section '%s' item '%s' because non-directory in output space." % (sect, name,)
                print errmsg
                failed[ (sect, name) ] = ( 0, errmsg, )
                continue
            else:
                p = subprocess.Popen(
                    [
                        'rm',
                        '-rf',
                        outdir,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )
                out = p.communicate()[0]
                if p.returncode!=0:
                    print "Couldn't clear old directory %s" % (outdir,)
                    print out
                    failed[ (sect, name) ] = ( p.returncode, "Deleting directory failed (%s)" % (out, ), )
                    continue
        os.mkdir(outdir)
        cwd = os.getcwd()
        os.chdir(outdir)
        vcsurl = value_to_url(value, name)
        print "%s: %s" % (name, vcsurl,)
        p = subprocess.Popen(
			checkout_cmd + [vcsurl],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        out = p.communicate()[0]
        if p.returncode!=0:
            print "Failed to download for section '%s' item '%s'" % (sect, name, )
            print out
            failed[ (sect, name) ] = ( p.returncode, out, )
        os.chdir(cwd)

def process_download(cp, sect, directory):
    for (name, value) in cp.items(sect):
        if name=='module' or name=='homepage':
            continue
        outdir = os.path.join(directory, name)
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        if not os.path.isdir(outdir):
            errmsg = "Could not process section '%s' item '%s' because non-directory in output space." % (sect, name,)
            print errmsg
            failed[ (sect, name) ] = ( 0, errmsg, )
            continue
        cwd = os.getcwd()
        os.chdir(outdir)
        print "%s: %s" % (name, value,)
        p = subprocess.Popen(
            [
                'wget',
                '-N', # overwrite if newer
                '--no-check-certificate', # does what it says on the tin
                value,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        out = p.communicate()[0]
        if p.returncode!=0:
            print "Failed to download for section '%s' item '%s'" % (sect, name, )
            print out
            failed[ (sect, name) ] = ( p.returncode, out, )
        os.chdir(cwd)

if __name__=="__main__":
    print "Ready to go?",
    parser = optparse.OptionParser()
    parser.add_option('-s', '--sources', dest='sources', help='Override default sources.where', default='sources.where', action='store')
    parser.add_option('-r', '--root', dest='root', help='Override output root', default='sources.downloaded', action='store')
    parser.add_option('-v', '--verbose', dest='verbose', help='Increase verbosity', default=False, action='store_true')
    (options, args) = parser.parse_args()

    cp = ConfigParser.ConfigParser()
    cp.read([options.sources])

    if len(args) > 0:
        sections = args
    else:
        sections = cp.sections()
    
    if not os.path.exists(options.root):
        os.mkdir(options.root)
    
    print "Good!"

    for sect in sections:
        print
        print "[%s]" % (sect,)
        directory = os.path.join(options.root, sect)
        if not os.path.exists(directory):
            os.mkdir(directory)
        if not os.path.isdir(directory):
            print "Could not process section '%s' because non-directory in output space." % (sect,)
            continue
        try:
            if cp.get(sect, 'skip')=='yes':
                print "Skipping."
                continue
        except ConfigParser.NoOptionError:
            pass
        try:
			module = cp.get(sect, 'module')
			if module=='github':
			    process_github(cp, sect, directory)
			    continue
			elif module=='subversion':
			    process_subversion(cp, sect, directory)
			    continue
			elif module=='git':
			    process_git(cp, sect, directory)
        except ConfigParser.NoOptionError:
            pass
        process_download(cp, sect, directory)
    
    if len(failed.keys()) > 0:
        print
        print "Some sections had problems:"
        print

        for (s, n) in failed.keys():
            if options.verbose:
                print "[%s]/%s: %s" % (s, n, failed[(s,n)][1],)
            else:
                print "[%s]/%s" % (s, n,)
