import difflib
import os
import requests
from keychain import __api_key__

class GitHubUploader:
    """
    Class for uploading patch files to GitHub
    """

    def __init__(self,
                 filename,
                 file_text,
                 sasview_version,
                 author,
                 changes,
                 branches_exist):

        self.filename = filename
        self.text = file_text
        self.version = sasview_version
        self.author = author
        self.changes = changes
        self.branch_exist = branches_exist

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
            old_ver = self.getOldVersion(commit_sha)
            patch = self.generatePatchString(old_ver, self.text)
            new_branch_name = f"patch-{self.version}"
            self.createBranch(new_branch_name, commit_sha)
            self.commitPatch(new_branch_name, patch, commit_sha)

    def getOldVersion(self, commit_sha):
        """Return the content of filename from commit_sha in GitHub"""
        if commit_sha:
            path_from_sas_folder = self.processFileName(self.filename)
            url = f"https://raw.githubusercontent.com/SasView/sasview/{commit_sha}/src/sas/{path_from_sas_folder}"
            response = requests.get(url)
            if response.status_code == 200:
                old_ver = response.text
                return old_ver
            else:
                print(f"Failed to retrieve file. Status code: {response.status_code}")
                print(f"Response content: {response.content}")
                print(f"Response headers: {response.headers}")  # TODO: Replace with some sort of error handling
                return None
        return None

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

    def generatePatchString(self, original: str, modified: str) -> str:
        """Generate a patch string from two strings."""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        # Create a unified diff
        diff = difflib.unified_diff(original_lines, modified_lines, lineterm='', n=0)
        
        # Join the diff lines into a single string
        patch = ''.join(diff)
        return patch

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

    def commitPatch(self, branch_name, patch, base_commit_sha):
        """Commit the patch to the new branch."""
        url = f"https://api.github.com/repos/SasView/sasview/git/commits"
        headers = {
            "Authorization": f"token {__api_key__}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Get the tree SHA of the latest commit
        commit_url = f"https://api.github.com/repos/SasView/sasview/git/commits/{base_commit_sha}"
        commit_response = requests.get(commit_url, headers=headers)
        commit_response.raise_for_status()
        tree_sha = commit_response.json()['tree']['sha']

        # Create a new blob with the patch content
        blob_url = f"https://api.github.com/repos/SasView/sasview/git/blobs"
        blob_data = {
            "content": patch,
            "encoding": "utf-8"
        }
        blob_response = requests.post(blob_url, json=blob_data, headers=headers)
        blob_response.raise_for_status()
        blob_sha = blob_response.json()['sha']

        # Create a new tree with the blob
        tree_url = f"https://api.github.com/repos/SasView/sasview/git/trees"
        tree_data = {
            "base_tree": tree_sha,
            "tree": [
                {
                    "path": "patch.diff",  # Specify the path to the file in the repo
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                }
            ]
        }
        tree_response = requests.post(tree_url, json=tree_data, headers=headers)
        tree_response.raise_for_status()
        new_tree_sha = tree_response.json()['sha']

        # Create a new commit
        commit_data = {
            "message": "Applied patch",
            "parents": [base_commit_sha],
            "tree": new_tree_sha
        }
        commit_response = requests.post(url, json=commit_data, headers=headers)
        commit_response.raise_for_status()
        new_commit_sha = commit_response.json()['sha']

        # Update the branch to point to the new commit
        ref_url = f"https://api.github.com/repos/SasView/sasview/git/refs/heads/{branch_name}"
        ref_data = {
            "sha": new_commit_sha
        }
        ref_response = requests.patch(ref_url, json=ref_data, headers=headers)
        ref_response.raise_for_status()
        return ref_response.json()


