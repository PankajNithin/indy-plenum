import os

import pytest
from crypto.bls.bls_crypto import BlsCryptoSigner
from crypto.bls.bls_key_manager import LoadBLSKeyError
from plenum.bls.bls_crypto_factory import BlsFactoryIndyCrypto
from plenum.common.config_util import getConfig
from state.pruning_state import PruningState
from storage.kv_in_memory import KeyValueStorageInMemory

config = getConfig()


@pytest.fixture()
def pool_state():
    return PruningState(KeyValueStorageInMemory())


@pytest.fixture()
def bls_crypto_factory(tempdir):
    os.mkdir(os.path.join(tempdir, 'Node1'))
    return BlsFactoryIndyCrypto(tempdir, 'Node1')


@pytest.fixture()
def bls_crypto_factory2(tempdir):
    os.mkdir(os.path.join(tempdir, 'Node2'))
    return BlsFactoryIndyCrypto(tempdir, 'Node2')


def test_create_and_store_bls_keys(bls_crypto_factory):
    pk = bls_crypto_factory.generate_and_store_bls_keys()
    assert pk
    assert isinstance(pk, str)


def test_create_bls_keys(bls_crypto_factory):
    sk, pk = bls_crypto_factory.generate_bls_keys()
    assert pk
    assert sk
    assert isinstance(sk, str)
    assert isinstance(pk, str)


def test_create_and_store_bls_keys_multiple(bls_crypto_factory):
    pk1 = bls_crypto_factory.generate_and_store_bls_keys()
    pk2 = bls_crypto_factory.generate_and_store_bls_keys()
    pk3 = bls_crypto_factory.generate_and_store_bls_keys()
    assert pk1 != pk2 != pk3


def test_create_bls_keys_multiple(bls_crypto_factory):
    sk1, pk1 = bls_crypto_factory.generate_bls_keys()
    sk2, pk2 = bls_crypto_factory.generate_bls_keys()
    sk3, pk3 = bls_crypto_factory.generate_bls_keys()
    assert pk1 != pk2 != pk3
    assert sk1 != sk2 != sk3


def test_create_bls_crypto_no_keys(bls_crypto_factory):
    with pytest.raises(LoadBLSKeyError):
        bls_crypto_factory.create_bls_crypto_signer_from_saved_keys()


def test_create_bls_crypto(bls_crypto_factory):
    pk = bls_crypto_factory.generate_and_store_bls_keys()
    bls_crypto_signer = bls_crypto_factory.create_bls_crypto_signer_from_saved_keys()
    assert bls_crypto_signer
    assert isinstance(bls_crypto_signer, BlsCryptoSigner)
    assert bls_crypto_signer._sk
    assert bls_crypto_signer.pk
    assert pk == bls_crypto_signer.pk


def test_create_bls_crypto_multiple_times(bls_crypto_factory):
    pk1 = bls_crypto_factory.generate_and_store_bls_keys()
    bls_crypto_signer1 = bls_crypto_factory.create_bls_crypto_signer_from_saved_keys()
    assert pk1 == bls_crypto_signer1.pk

    pk2 = bls_crypto_factory.generate_and_store_bls_keys()
    bls_crypto_signer2 = bls_crypto_factory.create_bls_crypto_signer_from_saved_keys()
    assert pk2 == bls_crypto_signer2.pk

    pk3 = bls_crypto_factory.generate_and_store_bls_keys()
    bls_crypto_signer3 = bls_crypto_factory.create_bls_crypto_signer_from_saved_keys()
    assert pk3 == bls_crypto_signer3.pk


def test_bls_crypto_works(bls_crypto_factory, bls_crypto_factory2):
    # create bls signer for Node1
    bls_crypto_factory.generate_and_store_bls_keys()
    bls_crypto_signer1 = bls_crypto_factory.create_bls_crypto_signer_from_saved_keys()
    pk1 = bls_crypto_signer1.pk

    # create bls signer for Node2
    bls_crypto_factory2.generate_and_store_bls_keys()
    bls_crypto_signer2 = bls_crypto_factory2.create_bls_crypto_signer_from_saved_keys()
    pk2 = bls_crypto_signer2.pk

    # create bls verifier
    bls_crypto_verifier = bls_crypto_factory.create_bls_crypto_verifier()

    # each node signs the message
    msg = 'Hello!'
    pks = [pk1, pk2]
    sigs = []
    sigs.append(bls_crypto_signer1.sign(msg))
    sigs.append(bls_crypto_signer2.sign(msg))

    # each node creates multi-sig
    multi_sig1 = bls_crypto_verifier.create_multi_sig(sigs)
    multi_sig2 = bls_crypto_verifier.create_multi_sig(sigs)

    # each node verifies multi-sigs
    assert bls_crypto_verifier.verify_multi_sig(multi_sig1, msg, pks)
    assert bls_crypto_verifier.verify_multi_sig(multi_sig2, msg, pks)
