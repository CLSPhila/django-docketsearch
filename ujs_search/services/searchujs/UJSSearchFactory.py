from .UJSSearch import UJSSearch

class UJSSearchFactory:
    """
    Class for searching the ujs portal using only python.


    It is initialized through a factory method, `use_court`, which takes the name of a court and 
    returns the Searcher that can search that court.
    """
    CP = "CP"
    MDJ = "MDJ"
    COURTS = [CP, MDJ]

    @classmethod
    def use_court(cls, court: str, **kwargs) -> UJSSearch:
        """
        Return the UJS Searcher the the given court.

        Args:
            court: either CP or MDJ

        Returns:
            a UJSSearcher for the `court`.
        """
        assert court in cls.COURTS, f"{court} is not a court we can search!"
        if court == cls.CP:
            from .CPSearch import CPSearch
            return CPSearch(**kwargs)
        else:
            from .MDJSearch import MDJSearch
            return MDJSearch(**kwargs)

