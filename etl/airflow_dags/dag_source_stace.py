from authentication.auth_stake import AuthenticationStake
from parsers.parser_stake import StakeParser
from transformers.transformer_stake import TransformerStake
from loaders.data_loader import DataLoader
from sdk.bet_save_sdk import BetSaveSDK
import asyncio
from utils.config.config import config
from xvfbwrapper import Xvfb



async def process_stake_data():
    """
    Main async function to process data from Stake.com.

    Workflow:
    1. Authentication:
        - Create an instance of AuthenticationStake with test credentials.
        - This handles login, human verification, and session initialization.
        - After calling login inside the parser, we have an active Browser, Context, and Page.

    2. Parsing:
        - Create a StakeParser instance with the authentication object.
        - Call `initialize_session()` to ensure the browser session is ready.
        - Use `parse_data()` to extract raw wagering data from Stake.com.
        - The parser returns structured data (dict or list of dicts).

    3. Transformation:
        - Create an instance of TransformerStake.
        - Call `transform()` on the parsed data to:
            a) Validate data against Pydantic models.
            b) Perform optional calculations (profit, totals, etc.).
            c) Standardize the data structure for BetSave API.
        - Returns a standardized BetSave model ready for loading.

    4. Data Loading:
        - Create an instance of DataLoader with a BetSaveSDK instance.
        - Send the standardized data using `send()`:
            - Handles single or bulk submissions automatically based on the `multiple` flag.
        - The SDK communicates with the BetSave API and logs responses.

    Notes:
        - Currently uses test credentials and URLs for development purposes.
        - The whole workflow is async to efficiently handle browser automation and network I/O.
    """

    with Xvfb(width=1920, height=1080, colordepth=24) as xvfb:
        # Step 1: Authentication
        auth = AuthenticationStake(
            base_url="https://stake.com",       # Test URL of Stake.com
            email=config.emailStake,           # Test email for login
            password=config.passwordStake,             # Test password
            headless=False # Headless browser mode for automation
        )

        # Step 2: Parsing
        parser = StakeParser(auth)
        await parser.initialize_session()  # Ensure browser session is active
        raw_data = await parser.parse_data()  # Extract data from Stake

        # Step 3: Transformation
        transformer = TransformerStake()
        standardized_data = await transformer.transform(raw_data)  # Validate, calculate, standardize

        # ============================================ ================================================== #
        # Step 4: Data Loading
        # sdk = BetSaveSDK(token=config.tokenAPI, base_url=config.baseUrlApi)  # Initialize BetSave SDK with test token and URL
        # loader = DataLoader(sdk)
        # response = await loader.send(standardized_data)  # Send data to BetSave
        #
        # # Log or print the response for debugging
        # print("DataLoader response:", response)


def run_process_stake_data():
    """
    Synchronous entry point to run the async process.
    Uses asyncio.run to execute the main async function.
    """
    asyncio.run(process_stake_data())
