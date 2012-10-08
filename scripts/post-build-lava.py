#!/usr/bin/python

import os
import sys
import json
import xmlrpclib
import urllib2
import re

tests_nano = [
    'device-tree',
    'gatortests',
    'perf',
    'pwrmgmt',
    ]


def obfuscate_credentials(s):
    return re.sub(r"([^ ]:).+?(@)", r"\1xxx\2", s)


def main():
    """Script entry point: return some JSON based on calling args.
    We should be called from Jenkins and expect the following to be defined:
    $HWPACK_BUILD_NUMBER $HWPACK_JOB_NAME HWPACK_FILE_NAME $DEVICE_TYPE
    """

    # CI base URL
    ci_base_url = "https://ci.linaro.org/jenkins/job/"
    # Snapshots base URL
    snapshots_url = "http://snapshots.linaro.org"

    # Name of the hardware pack project
    hwpack_job_name = os.environ.get("HWPACK_JOB_NAME")
    # The hardware pack build number
    hwpack_build_number = os.environ.get("HWPACK_BUILD_NUMBER")
    # Hardware pack file name
    hwpack_file_name = os.environ.get("HWPACK_FILE_NAME", "Undefined")
    if hwpack_file_name == "Undefined":
        sys.exit("Hardware pack is not defined.")
    # Device type
    device_type = os.environ.get("DEVICE_TYPE", "Undefined")
    if device_type == "Undefined":
        sys.exit("Device type is not defined.")

    # Distribution, architecture and hardware pack type
    if hwpack_job_name.startswith('package-and-publish'):
        ret_split = hwpack_job_name.split("-", 3)
        distribution = 'precise'
        architecture = 'armhf'
        hwpack_type = ret_split[3]
    else:
        ret_split = hwpack_job_name.split("-", 2)
        (distribution, architecture, hwpack_type) = \
            ret_split[0], ret_split[1], ret_split[2]
    # Rootfs type, default is nano-lava
    rootfs_type = os.getenv("ROOTFS_TYPE", "nano-lava")

    # Bundle stream name
    bundle_stream_name = os.environ.get("BUNDLE_STREAM_NAME", \
        "/private/team/linaro/developers-and-community-builds/")
    # LAVA user
    lava_user = os.environ.get("LAVA_USER")
    if lava_user == None:
        f = open('/var/run/lava/lava-user')
        lava_user = f.read().strip()
        f.close()
    # LAVA token
    lava_token = os.environ.get("LAVA_TOKEN")
    if lava_token == None:
        f = open('/var/run/lava/lava-token')
        lava_token = f.read().strip()
        f.close()
    # LAVA server URL
    lava_server = os.environ.get("LAVA_SERVER", \
        "validation.linaro.org/lava-server/RPC2/")
    # LAVA server base URL
    lava_server_root = lava_server.rstrip("/")
    if lava_server_root.endswith("/RPC2"):
        lava_server_root = lava_server_root[:-len("/RPC2")]

    # Rootfs last successful build number
    ci_url = "%s%s-%s-%s%s" % \
             (ci_base_url, \
              distribution, \
              architecture, \
              rootfs_type, \
              "/lastSuccessfulBuild/buildNumber")
    request = urllib2.Request(ci_url)
    try:
        response = urllib2.urlopen(request)
    except urllib2.URLError, e:
        if hasattr(e, 'reason'):
            print 'Failed to reach %s.' % ci_url
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'ci.linaro.org could not fulfill the request.'
            print 'Error code: ', e.code
        sys.exit("Failed to get last successful rootfs build number.")

    rootfs_build_number = eval(response.read())

    # Rootfs last successful build timestamp
    ci_url = "%s%s-%s-%s%s" % \
             (ci_base_url, \
              distribution, \
              architecture, \
              rootfs_type, \
              "/lastSuccessfulBuild/buildTimestamp?format=yyyyMMdd")
    request = urllib2.Request(ci_url)
    try:
        response = urllib2.urlopen(request)
    except urllib2.URLError, e:
        if hasattr(e, 'reason'):
            print 'Failed to reach %s.' % ci_url
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'ci.linaro.org could not fulfill the request.'
            print 'Error code: ', e.code
        sys.exit("Failed to get last successful rootfs build timestamp.")

    rootfs_build_timestamp = eval(response.read())

    rootfs_file_name = "linaro-%s-%s-%s-%s.tar.gz" % \
                       (distribution, \
                        rootfs_type, \
                        rootfs_build_timestamp, \
                        rootfs_build_number)

    # Convert CI URLs to snapshots URLs
    if hwpack_job_name.startswith('package-and-publish'):
        hwpack_job_name_fixup = hwpack_job_name.replace('.', '_')
        hwpack_url = "%s/%s/%s/%s/%s/%s" % \
                     (snapshots_url, \
                      "kernel-hwpack",\
                      hwpack_job_name_fixup, \
                      hwpack_job_name, \
                      hwpack_build_number, \
                      hwpack_file_name)
    else:
        hwpack_url = "%s/%s/%s/%s/%s/%s" % \
                     (snapshots_url, \
                      distribution, \
                      "hwpacks", \
                      hwpack_type, \
                      hwpack_build_number, \
                      hwpack_file_name)

    rootfs_url = "%s/%s/%s/%s/%s/%s" % \
                 (snapshots_url, \
                  distribution, \
                  "images", \
                  rootfs_type, \
                  rootfs_build_number, \
                  rootfs_file_name)

    # tests set specific to an image
    tests = tests_nano

    # vexpress doesn't support PM, so disable pwrmgmt
    if device_type in ['vexpress-a9']:
        try:
            tests.remove('pwrmgmt')
        except ValueError:
            pass

    actions = [{
        "command": "deploy_linaro_image",
        "parameters": {
                "hwpack": "%s" % hwpack_url,
                "rootfs": "%s" % rootfs_url
        },
        "metadata": {
                "hwpack.type": "%s" % hwpack_type,
                "hwpack.build": "%s" % hwpack_build_number,
                "rootfs.type": "%s" % rootfs_type,
                "rootfs.build": "%s" % rootfs_build_number,
                "distribution": "%s" % distribution
        }
    },
    {
        "command": "boot_linaro_image"
    }]

    for test in tests:
        actions.append({
            "command": "lava_test_run",
            "parameters": {
                "test_name": test
            }
        })

    actions.append({
        "command": "submit_results",
        "parameters": {
            "stream": bundle_stream_name,
            "server": "%s%s" % ("http://", lava_server)
        }
    })

    config = json.dumps({"timeout": 18000,
                         "actions": actions,
                         "job_name": "%s%s/%s/" % (ci_base_url, \
                                                   hwpack_job_name, \
                                                   hwpack_build_number),
                         "device_type": device_type,
                        }, indent=2)

    print config

    skip_lava = os.environ.get("SKIP_LAVA")
    if skip_lava == None:
        try:
            server_url = \
                "https://{lava_user:>s}:{lava_token:>s}@{lava_server:>s}"
            server = \
                xmlrpclib.ServerProxy(server_url.format(\
                    lava_user=lava_user, \
                    lava_token=lava_token, \
                    lava_server=lava_server))
            lava_job_id = server.scheduler.submit_job(config)
        except xmlrpclib.ProtocolError, e:
            print "Error making a LAVA request:", obfuscate_credentials(str(e))
            sys.exit(1)

        print "LAVA Job Id: %s, URL: http://%s/scheduler/job/%s" % \
              (lava_job_id, lava_server_root, lava_job_id)
        json.dump({'lava_url': "http://" + lava_server_root,
                   'job_id': lava_job_id},
                   open('lava-job-info', 'w'))
    else:
        print "LAVA job submission skipped."

if __name__ == "__main__":
        main()
