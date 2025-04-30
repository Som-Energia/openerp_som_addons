from yamlns import namespace as ns


def assertNsEqual(self, dict1, dict2):  # copied from plantmeter/testutils.py
    """
    Asserts that both dict have equivalent structure.
    If parameters are strings they are parsed as yaml.
    Comparation by comparing the result of turning them
    to yaml sorting the keys of any dict within the structure.
    """
    def parseIfString(nsOrString):
        if isinstance(nsOrString, dict):
            return nsOrString
        return ns.loads(nsOrString)

    def sorteddict(d):
        if type(d) in (dict, ns):
            return ns(sorted(
                (k, sorteddict(v))
                for k, v in d.items()
            ))
        if type(d) in (list, tuple):
            return [sorteddict(x) for x in d]
        return d
    dict1 = sorteddict(parseIfString(dict1))
    dict2 = sorteddict(parseIfString(dict2))

    return self.assertMultiLineEqual(dict1.dump(), dict2.dump())
