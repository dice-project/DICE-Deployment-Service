
class CfyMockupSuccess(Exception):
    """ Raised when mocking CfyClient and result should be SUCCESS """
    pass


class CfyMockupFail(Exception):
    """ Raised when mocking CfyClient and result should be FAIL """
    pass
