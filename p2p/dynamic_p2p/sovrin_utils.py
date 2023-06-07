from indy import wallet, did, pairwise, pool, IndyError


async def create_wallet(wallet_name: str, wallet_pass: str) -> str:
    try:
        await wallet.create_wallet('pool', wallet_name, None, None, wallet_pass)
        wallet_handle = await wallet.open_wallet(wallet_name, None, wallet_pass)
        return wallet_handle
    except IndyError as e:
        print(f'Error creating wallet: {e}')

async def create_did(wallet_handle: str) -> str:
    try:
        (did, ver_key) = await did.create_and_store_my_did(wallet_handle, '{}')
        return did
    except IndyError as e:
        print(f'Error creating DID: {e}')

async def create_pairwise(wallet_handle: str, my_did: str, their_did: str, their_ver_key: str):
    try:
        metadata = '{"some_key": "some_value"}'
        await pairwise.create_pairwise(wallet_handle, their_did, my_did, metadata)
        await pairwise.set_pairwise_metadata(wallet_handle, their_did, metadata)
    except IndyError as e:
        print(f'Error creating pairwise connection: {e}')

async def authenticate_user(wallet_name: str, wallet_pass: str, their_did: str) -> bool:
    try:
        pool_handle = await pool.open_pool_ledger('pool', None)
        wallet_handle = await wallet.open_wallet(wallet_name, None, wallet_pass)

        pairwise_info = await pairwise.get_pairwise(wallet_handle, their_did)
        if not pairwise_info:
            return False

        their_ver_key = pairwise_info['metadata']['their_verkey']
        their_did_info = await did.get_did_with_meta(pool_handle, wallet_handle, their_did)
        their_ver_key_from_ledger = their_did_info['verkey']

        if their_ver_key != their_ver_key_from_ledger:
            return False

        await wallet.close_wallet(wallet_handle)
        await pool.close_pool_ledger(pool_handle)

        return True
    except IndyError as e:
        print(f'Error authenticating user: {e}')
        return False