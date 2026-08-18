
from dataclasses import dataclass 

from core .unified_config import load_section ,save_section 


@dataclass 
class GitCredentials :
    github_url :str =""
    token :str =""
    git_exe_path :str =""

    @classmethod 
    def load (cls ,base_dir :str )->"GitCredentials":
        data =load_section (base_dir ,"git_credentials")
        return cls (
        github_url =data .get ("github_url",""),
        token =data .get ("token",""),
        git_exe_path =data .get ("git_exe_path",""),
        )

    def save (self ,base_dir :str ):
        save_section (base_dir ,"git_credentials",{
        "github_url":self .github_url ,
        "token":self .token ,
        "git_exe_path":self .git_exe_path ,
        })
