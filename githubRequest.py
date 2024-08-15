import datetime
import difflib
import os
import requests

from IDDatabase import access_database
from keychain import __api_key__
from version import __version__

class GitHubUploader:
    """
    Class for uploading files to GitHub
    """

    def __init__(self,
                 filename,
                 file_text,
                 sasview_version,
                 author,
                 changes,
                 branches_exist,
                 root_url):

        self.filename = filename
        self.text = file_text
        self.version = sasview_version
        self.author = author
        self.changes = changes
        self.branch_exist = branches_exist
        self.root_url = root_url

        self.response = None

        self.version = self.processVersioning(self.version)

        self.__main()

    def __main(self) -> None:
        commit_sha = self.getCommitShaFromTag(self.version, token=__api_key__)
        print(commit_sha)
        if self.branch_exist:
            # TODO: Find existing branch
            pass
        else:
            if self.getOldVersion(commit_sha):
                # Branch name must conform to github's branch naming conventions
                new_branch_name = f"(user-{self.version}){os.path.basename(self.filename)}" 
                self.createBranch(new_branch_name, commit_sha)
                self.commitNewVersion(new_branch_name, self.text, commit_sha)
                self.createPullRequest(new_branch_name)
                self.response = "Upload successful"
            else:
                print("File does not exist in the specified commit SHA.")

    def getOldVersion(self, commit_sha):
        """Check if the filename exists in the specified commit SHA on GitHub."""
        if commit_sha:
            path_from_sas_folder = self.processFileName(self.filename)
            url = f"https://raw.githubusercontent.com/SasView/sasview/{commit_sha}/src/sas/{path_from_sas_folder}"
            response = requests.get(url)
            if response.status_code == 200:
                return True
            else:
                print(f"File does not exist. Status code: {response.status_code}")
                return False
        return False

    def processVersioning(self, version: str):
        """
        Not a great way of processing versions but it works for now.
        """
        if 'b' in version:
            version = version.replace('b', '-beta-')
        if not version.startswith('v'):
            version = 'v' + version
        return version

    def processFileName(self, filename: str) -> str | None:
        """Return all of a filename after the 'user' directory.
        Change backslashes to forward slashes.
        Insert '/media' before the last slash.
        """
        user_dir = os.path.join('user', '')  # Add trailing slash for exact match
        index = filename.find(user_dir)
        if index != -1:
            # Extract the relevant part of the filename and replace backslashes with forward slashes
            processed_filename = filename[index + len(user_dir):].replace('\\', '/')
            # Find the last slash in the processed filename
            last_slash_index = processed_filename.rfind('/')
            if last_slash_index != -1:
                # Insert '/media' before the last slash
                return processed_filename[:last_slash_index] + '/media' + processed_filename[last_slash_index:]
            else:
                return '/media' + processed_filename  # If no slash is found, add '/media' at the beginning
        else:
            return None

    def getCommitShaFromTag(self, version, token=None):
        """
        Get the commit SHA associated with a specific tag.
        """
        url = f"https://api.github.com/repos/SasView/sasview/git/ref/tags/{version}"
        headers = {"Authorization": f"token {token}"} if token else {}
        
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data.get('object', {}).get('sha')
        else:
            print(f"Failed to retrieve commit SHA from tag. Status code: {response.status_code}")
            print(f"Response content: {response.content}")
            print(f"Response headers: {response.headers}")
            return None

    def createBranch(self, branch_name, commit_sha):
        """Create a new branch in the repository."""
        url = f"https://api.github.com/repos/SasView/sasview/git/refs"
        headers = {
            "Authorization": f"token {__api_key__}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": commit_sha
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def commitNewVersion(self, branch_name, new_content, base_commit_sha):
        """Commit the new version of the file to the specified branch."""
        path_from_sas_folder = self.processFileName(self.filename)
        
        # Step 1: Get the current tree SHA of the latest commit
        url = f"https://api.github.com/repos/SasView/sasview/git/trees/{base_commit_sha}"
        headers = {
            "Authorization": f"token {__api_key__}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tree_sha = response.json()['sha']

        # Step 2: Create a new blob with the updated file content
        blob_url = f"https://api.github.com/repos/SasView/sasview/git/blobs"
        blob_data = {
            "content": new_content,
            "encoding": "utf-8"
        }
        blob_response = requests.post(blob_url, json=blob_data, headers=headers)
        blob_response.raise_for_status()
        blob_sha = blob_response.json()['sha']

        # Step 3: Create a new tree with the updated file
        tree_url = f"https://api.github.com/repos/SasView/sasview/git/trees"
        tree_data = {
            "base_tree": tree_sha,
            "tree": [
                {
                    "path": f"src/sas/{path_from_sas_folder}",
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                }
            ]
        }
        tree_response = requests.post(tree_url, json=tree_data, headers=headers)
        tree_response.raise_for_status()
        new_tree_sha = tree_response.json()['sha']

        # Step 4: Create a new commit with the updated tree
        commit_url = f"https://api.github.com/repos/SasView/sasview/git/commits"
        commit_data = {
            "message": self.changes,
            "parents": [base_commit_sha],
            "tree": new_tree_sha
        }
        commit_response = requests.post(commit_url, json=commit_data, headers=headers)
        commit_response.raise_for_status()
        new_commit_sha = commit_response.json()['sha']

        # Step 5: Update the branch to point to the new commit
        ref_url = f"https://api.github.com/repos/SasView/sasview/git/refs/heads/{branch_name}"
        ref_data = {
            "sha": new_commit_sha
        }
        ref_response = requests.patch(ref_url, json=ref_data, headers=headers)
        ref_response.raise_for_status()
        return ref_response.json()

    def getID(self):
        """Get unique ID for the request."""
        id = access_database(self.filename)
        id = str(id).zfill(6) # Pad with zeros
        return id

    def createPullRequest(self, branch_name):
        """Create a pull request for the new branch."""
        url = f"https://api.github.com/repos/SasView/sasview/pulls"
        headers = {
            "Authorization": f"token {__api_key__}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": f"User Patch for {os.path.basename(self.filename)} ({self.version})",
            "head": branch_name,
            "base": "main",
            "body": self.getBody()
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def getBody(self):
        """
        Generate the body of the pull request.
        """
        return f"""\
## Patch for {os.path.basename(self.filename)} ({self.version})
Author: {self.author}
SasView Version: {self.version}

### Changes
{self.changes}

### Log
```
api: v.{__version__}
time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
root: {self.root_url}
request_id: {self.getID()}
```
"""
