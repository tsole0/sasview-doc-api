import requests
from keychain import __api_key__

class GitHubUploader():
    """
    Class for uploading patch files to github
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
        self.branch = branches_exist

        self.response = None

        self.version = self.processVersioning(self.version)

        self.getCommitShaFromTag(self.version, token=__api_key__)

    def processVersioning(self, version: str):
        if 'b' in version:
            return version.replace('b', '-beta-')
    
    def getCommitShaFromTag(self, version, token=None):
        """
        Get the commit SHA associated with a specific release tag.

        :param owner: The owner of the repository.
        :param repo: The repository name.
        :param tag: The release tag.
        :param token: (Optional) GitHub personal access token for authentication.
        :return: The commit SHA or None if not found.
        """
        url = f"https://api.github.com/repos/SasView/sasview/releases/tags/{version}"
        headers = {}
        
        if token:
            headers['Authorization'] = f"token {token}"
        
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data.get('target_commitish')
        else:
            print(f"Failed to retrieve release information. Status code: {response.status_code}")
            print(f"Response content: {response.content}")
            print(f"Response headers: {response.headers}")
            return None

