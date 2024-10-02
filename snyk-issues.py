import argparse
import snyk
import os
from urllib.parse import quote
import httpx
import logging
import json
from git import Repo

'''
Description: Program meant to:
 query Snyk Projects
 query types of targets in orgs
 tag github with those targets to run enforcement
'''
token = os.getenv('SNYK_API_TOKEN') # Set your API token as an environment variable
apiVersion = "2024-04-11~beta"  # Set the API version. Needs ~beta endpoint at stated version or later
tries = 4  # Number of retries
delay = 1  # Delay between retries
backoff = 2  # Backoff factor

remote_repo_url = None
tag_value = None

def set_org_tag():
    client = snyk.SnykClient(token, tries=tries, delay=delay, backoff=backoff)  # Context switch the client to model-based
    organizations = client.organizations.all()

    for org in organizations:
        projects = org.projects.all()
        for project in projects:
            print(f"project remoterepourl {project.remoteRepoUrl} and our local remote_repo_url {remote_repo_url}")
            if project.remoteRepoUrl == remote_repo_url:
                with create_client(token=token, tenant="us") as client:
                    #tag project
                    print(f"org id {org.id} project {project.id} tag_value:{tag_value} project name: {project.name}")
                    apply_tag_to_project(client, org.id, project.id, "testKey", tag_value, project.name)

def apply_tag_to_project(
    client: httpx.Client,
    org_id: str,
    project_id: str,
    tag: str,
    key: str,
    project_name: str,
) -> tuple:
    tag_data = {
        "key": key,
        "value": tag,
    }
    req = client.post(
        f"org/{org_id}/project/{project_id}/tags", data=tag_data, timeout=None
    )

    if req.status_code == 200:
        logging.info(f"Successfully added {tag} tag to Project: {project_name}.")
    elif req.status_code == 422:
        logging.warning(f"{tag} tag is already applied for Project: {project_name}.")
    elif req.status_code == 404:
        logging.error(
            f"Project not found, likely a READ-ONLY project. Project: {project_name}. Error message: {req.json()}."
        )
    return req.status_code, req.json()

def read_config_file()->str:
    global tag_value

    openfile = open(".gitlab-ci.yml")
    jsonreader = json.load(openfile)
    
    #for row in jsonreader:
    #    tag_value = row.get("organization")

    tag_value = jsonreader["organization"]
    openfile.close()

def read_git_config()->str:
    global remote_repo_url

    repo = Repo("./")
    assert not repo.bare




# Reach to the API and generate tokens
def create_client(token: str, tenant: str) -> httpx.Client:
    base_url = (
        f"https://api.{tenant}.snyk.io/v1"
        if tenant in ["eu", "au"]
        else "https://api.snyk.io/v1"
    )
    headers = {"Authorization": f"token {token}"}
    return httpx.Client(base_url=base_url, headers=headers)

if __name__ == '__main__':
    # Parsing Command Line Arguments
    parser = argparse.ArgumentParser(
        description='Tag Snyk Org from .gitlab-ci.yml')
    # Required fields:

    read_git_config()
    read_config_file()

    if tag_value is not None:
        set_org_tag()   
    else: 
        "couldn't read tag from .gitlab-ci.yml"

    print(f"--------------------")
    print(f'Collecting Project Types:')
    print(f"--------------------")

    # print count of issues with description of filter criteria from arguments
    print(f"\n")

    exit()