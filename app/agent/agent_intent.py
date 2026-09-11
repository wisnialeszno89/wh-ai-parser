from enum import Enum


class AgentIntent(str, Enum):
    CREATE_QUOTE = "create_quote"
    MODIFY_QUOTE = "modify_quote"
    CHECK_TECHNICAL = "check_technical"
    COMPARE_VARIANTS = "compare_variants"
    CHECK_MARKET = "check_market"
    WRITE_CUSTOMER_REPLY = "write_customer_reply"
    EXECUTE_IN_WH = "execute_in_wh"
    OBSERVE_WORKFLOW = "observe_workflow"
    HELP = "help"
    UNKNOWN = "unknown"
