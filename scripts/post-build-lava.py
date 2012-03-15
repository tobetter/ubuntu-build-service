#!/usr/bin/env python

import os
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
    device_type = os.environ.get("DEVICE_TYPE", "panda")
    # Hardware pack name
    hwpack_name = os.environ.get("HWPACK_NAME", "hwpack_linaro-lt-panda_20120313-0_armhf_supported.tar.gz")
    # Hardware pack date
    hwpack_date = os.environ.get("HWPACK_DATE", "20120313")
    # Rootfs type
    rootfs_type = os.getenv("ROOTFS_TYPE", "nano")
    # Bundle stream name
    bundle_stream_name = os.environ.get("BUNDLE_STREAM_NAME", "/anonymous/fabo/")
    # LAVA user
    lava_user = os.environ.get("LAVA_USER", "ciadmin")
    # LAVA token
    lava_token = os.environ.get("LAVA_TOKEN")
    # LAVA server URL
    lava_server = os.environ.get("LAVA_SERVER", "validation.linaro.org/lava-server/RPC2/")
    # LAVA server base URL
    lava_server_root = lava_server.rstrip("/")
    if lava_server_root.endswith("/RPC2"):
        lava_server_root = lava_server_root[:-len("/RPC2")]

    rootfs_build = eval(urllib2.urlopen("%s%s" % (download_url, "precise-armhf-nano/lastSuccessfulBuild/buildNumber")).read())

    actions = [{
        "command": "deploy_linaro_image",
        "parameters": {
                "hwpack": "%s%s%s" % (build_url, "artifact/", hwpack_name) ,
                "rootfs": "%s%s" % (download_url, "precise-armhf-nano/lastSuccessfulBuild/artifact/binary-tar.tar.gz")
        },
        "metadata": {
                "hwpack.type": "%s" % job_name,
                "hwpack.date": "%s" % hwpack_date,
                "hwpack.build": "%s" % build_number,
                "rootfs.type": "precise-armhf-nano",
                "rootfs.date": "20120313",
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

    server = xmlrpclib.ServerProxy("https://{lava_user:>s}@{lava_server:>s}".format(lava_user=lava_user, lava_server=lava_server))
    server_token = xmlrpclib.ServerProxy("https://{lava_user:>s}:{lava_token:>s}@{lava_server:>s}".format(lava_user=lava_user, lava_token=lava_token, lava_server=lava_server))
    lava_job_id = "XXXXX" # server.scheduler.submit_job(config)

    print "LAVA Job Id: %s, URL: http://%s/scheduler/job/%s" % (lava_job_id, lava_server_root, lava_job_id)

    json.dump({'lava_url': "http://" + lava_server_root,
               'job_id': lava_job_id},
               open('lava-job-info', 'w'))

if __name__ == "__main__":
        main()
