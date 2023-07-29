def topological_sort_util(v, visited, stack, graph):
    """
    A helper function for the topological sort function.
    
    Args:
    v: The node to start the traversal from.
    visited: A set to keep track of visited nodes.
    stack: A list to store the topological order.
    graph: The adjacency list representation of the graph.
    """
    
    # Mark the current node as visited.
    visited.add(v)
    
    # Visit all the neighbours.
    for neighbour in graph.get(v, []):
        if neighbour not in visited:
            topological_sort_util(neighbour, visited, stack, graph)
    
    # Add the node to the stack.
    stack.insert(0, v)


def topological_sort(graph):
    """
    The function to perform topological sort.
    
    Args:
    graph: The adjacency list representation of the graph.
    """
    
    # Create a set to keep track of visited nodes.
    visited = set()
    
    # A list to store the topological order.
    stack = []
    
    # Visit all the nodes.
    for node in graph:
        if node not in visited:
            topological_sort_util(node, visited, stack, graph)
    
    return stack


def get_dependency_order(dependency_dict):
    """
    The function to get the order of dependencies.
    
    Args:
    dependency_dict: The dictionary representing dependencies.
    """
    
    # Create an adjacency list representation of the graph.
    graph = {}
    for app, classes in dependency_dict.items():
        for class_name, dependencies in classes.items():
            graph[class_name] = dependencies
    
    # Perform topological sort on the graph.
    dependency_order = topological_sort(graph)
    
    return dependency_order