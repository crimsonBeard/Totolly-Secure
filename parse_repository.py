"""
<Program Name>
    parse_repository.py

<Authors>
    Team Totolly Secure

<Started>
    November 2015.



<Purpose>
    The following shell command recurses through metadata, detect
    workflow paterns, and log its findings especially those findings
    that are strange when compared to the rest of the pattern.
    Workflows may be of any style.
"""

from subprocess import check_output
import json, metadata_lib

# hashes of commits that were already touched
hashes = []

# metadata dictionary
metadata = {}

def add_child( parent_hash, child_hash ) :
    """
    <Purpose>
        This function assigns child nodes to metadata for the current node.
        Value added will be the child hash.
    
    <Arguments>
        Parent and childs' hashes.
    
    <Exceptions>
        None. Program will fail silently if algorithm is not found.
    
    <Returns>
        Nothing.
    """
    
    global metadata

    child_num = 2

    while True :
        child = "child"+`child_num`

        if child in metadata[parent_hash] :
            child_num += 1
        else :
            metadata[parent_hash][child] = child_hash
            break

def add_timestamps( commit_hash ) :
    """
    <Purpose>
        This function adds timestamps to metadata associated with action.
    
    <Arguments>
        Committer's hash and a bool value indicating whether action
        is a merge or not.
    
    <Exceptions>
        None. Program will fail silently if algorithm is not found.
    
    <Returns>
        Nothing.
    """
    global metadata

    metadata[commit_hash]["author_timestamp"] = check_output(
        ["git", "show", "-s", "--format=%ai", commit_hash]
        ).strip( )

    metadata[commit_hash]["commit_timestamp"] = check_output(
        ["git", "show", "-s", "--format=%ci", commit_hash]
        ).strip( )

# for now types include: HEAD, TAIL, commit, pre-branch/fork. amd merge
def add_type( commit_hash, commit_type ) :
    """
    <Purpose>
        Adds the "Type" of action attribute to the metadata.
    
    <Arguments>
        The commit's hash and commit's type from another call is required.
    
    <Exceptions>
        None. Program will fail silently if algorithm is not found.
    
    <Returns>
        Nothing.
    """
    
    global metadata

    if len( metadata[commit_hash]["type"] ) == 0 :
        metadata[commit_hash]["type"] = commit_type
    else :
        # could be "pre-branch/fork" and "merge" simultaneously
        metadata[commit_hash]["type"] += "; "+commit_type

# Recurse thought the tree until the initial commit is reached.
def traverse( commit_hash, child_hash = None ) :
    """
    <Purpose>
        This function takes in the HEAD node and recurses backwards
        while visiting each node.
    
    <Arguments>
        HEAD node.
    
    <Exceptions>
        None. Program will fail silently if algorithm is not found.
    
    <Returns>
        Nothing.
    """
    
    global metadata

    metadata[commit_hash] = {}
    metadata[commit_hash]["type"] = ""

    if child_hash :
        metadata[commit_hash]["child1"] = child_hash

    # text of the current git commit object
    # elements of current_commit are in the format "<label> <value>"
    current_commit = check_output(
        ["git", "cat-file", "-p", commit_hash]
        ).split( "\n" )
    
    # parents of the current commit
    parents = []
    merge = False

    # find all parents of the current commit
    for line in current_commit :
        if len( line ) != 0 :
            if line.startswith( "parent" ) :
                parents.append( line )
            elif line.startswith( "author" ) :
                author = line.split( " ", 1 )[1]
                metadata[commit_hash]["author"] = \
                    author[:author.find( ">" )+1]
            elif line.startswith( "committer" ) :
                committer = line.split( " ", 1 )[1]
                metadata[commit_hash]["committer"] = \
                    committer[:committer.find( ">" )+1]

    add_timestamps( commit_hash )

    if len( parents ) > 0 :
        for x in range( 0, len( parents )  ) :
            parent_hash = parents[x].split( )[1]

            metadata[commit_hash]["parent"+`x+1`] = parent_hash

            global hashes
            if parent_hash not in hashes :
                hashes.append( parent_hash )
                traverse( parent_hash, commit_hash )
            else :
                add_child( parent_hash, commit_hash )


# hash of the HEAD commit
head = check_output( ["git", "rev-parse", "HEAD"] ).strip( )
hashes.append( head )
traverse( head )

for commit in metadata :
    if "parent2" in metadata[commit] :
        # if there are two or more parents, it's a merge commit
        add_type( commit, "merge" )
    elif "parent1" not in metadata[commit] :
        # if there are no parents, it's the tail commit
        add_type( commit, "TAIL" )

    if "child2" in metadata[commit] :
        # if there are two or more children, it's a pre-branch/fork commit
        add_type( commit, "pre-branch/fork" )
    elif "child1" not in metadata[commit] :
        # if there are no children, it's a HEAD commit
        # (with respect to the current branch)
        add_type( commit, "HEAD" )

    if "parent2" not in metadata[commit] and \
        "child2" not in metadata[commit] :
        # if there are neither multiple parents nor multiple children,
        # it's a normal commit
        add_type( commit, "commit" )

with open( "metadata.json", "w" ) as ofs :
    ofs.write( json.dumps( metadata, indent = 4 ) )
