#!/usr/bin/env python

import os
import sys
import json
import xmlrpclib
import urllib2

def main():
    """Script entry point: return some JSON based on calling args.
    We should be called from Jenkins and expect the following to 
    be defined: $BUILD_NUMBER $JOB_NAME $BUILD_URL DEVICE
    """

    # The current build number, defined by Jenkins
    build_number = os.environ.get("BUILD_NUMBER")
    # Name of the project of this build, defined by Jenkins
    job_name = os.environ.get("JOB_NAME")
    # Full URL of this job, defined by Jenkins
    build_url = os.environ.get("BUILD_URL")
    # Download base URL, this may differ from build URL
    download_url = "https://ci.linaro.org/jenkins/job/"
    # Device type
    device_type = os.environ.get("DEVICE_TYPE", "Undefined")
    if device_type == "Undefined":
        sys.exit("Device type is not defined.")
    # Hardware pack name
    hwpack_name = os.environ.get("HWPACK_NAME", "Undefined")
    if hwpack_name == "Undefined":
        sys.exit("Hardware pack is not defined.")
    # Rootfs type
    rootfs_type = os.getenv("ROOTFS_TYPE", "nano")
    # Rootfs job name
    rootfs_job_name = job_name.rsplit("-",2)
    rootfs_job_name = "%s-%s" % (rootfs_job_name[0], rootfs_type)
    # Bundle stream name
    bundle_stream_name = os.environ.get("BUNDLE_STREAM_NAME", "/anonymous/fabo/")
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
    lava_server = os.environ.get("LAVA_SERVER", "validation.linaro.org/lava-server/RPC2/")
    # LAVA server base URL
    lava_server_root = lava_server.rstrip("/")
    if lava_server_root.endswith("/RPC2"):
        lava_server_root = lava_server_root[:-len("/RPC2")]

    rootfs_build = eval(urllib2.urlopen("%s%s%s" % (download_url, rootfs_job_name, "/lastSuccessfulBuild/buildNumber")).read())

    actions = [{
        "command": "deploy_linaro_image",
        "parameters": {
                "hwpack": "%s%s%s" % (build_url, "artifact/", hwpack_name) ,
                "rootfs": "%s%s%s%s%s" % (download_url, rootfs_job_name, "/", rootfs_build, "/artifact/binary-tar.tar.gz")
        },
        "metadata": {
                "hwpack.type": "%s" % job_name,
                "hwpack.build": "%s" % build_number,
                "rootfs.type": "%s" % rootfs_job_name,
                "rootfs.build": "%s" % rootfs_build
        }
    },
    {
        "command": "boot_linaro_image"
    },
    {
        "command": "submit_results",
        "parameters": {
            "stream": bundle_stream_name,
            "server": "%s%s" % ("http://", lava_server)
        }
    }]

    config = json.dumps({"timeout": 18000,
                         "actions": actions,
                         "job_name": "%s%s" % ("CI - ", job_name),
                         "device_type": device_type,
                        }, indent=2)

    print config

    server = xmlrpclib.ServerProxy("https://{lava_user:>s}:{lava_token:>s}@{lava_server:>s}".format(lava_user=lava_user, lava_token=lava_token, lava_server=lava_server))
    lava_job_id = server.scheduler.submit_job(config)

    print "LAVA Job Id: %s, URL: http://%s/scheduler/job/%s" % (lava_job_id, lava_server_root, lava_job_id)

    json.dump({'lava_url': "http://" + lava_server_root,
               'job_id': lava_job_id},
               open('lava-job-info', 'w'))

if __name__ == "__main__":
        main()
