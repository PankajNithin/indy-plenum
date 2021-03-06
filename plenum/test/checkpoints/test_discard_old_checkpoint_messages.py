from stp_core.loop.eventually import eventually
from plenum.common.messages.node_messages import Checkpoint
from plenum.test.checkpoints.helper import chkChkpoints
from plenum.test.helper import checkDiscardMsg
from plenum.test.sdk.conftest import sdk_pool_name, sdk_pool_handle, sdk_wallet_name,\
    sdk_wallet_handle, sdk_wallet_client, sdk_client_seed
from plenum.test.sdk.helper import send_random_and_check


def test_discard_checkpoint_msg_for_stable_checkpoint(chkFreqPatched, looper, txnPoolNodeSet, sdk_pool_handle,
                                                      sdk_wallet_client, reqs_for_checkpoint):
    send_random_and_check(looper, txnPoolNodeSet, sdk_pool_handle, sdk_wallet_client, reqs_for_checkpoint)
    looper.run(eventually(chkChkpoints, txnPoolNodeSet, 1, 0, retryWait=1))
    node1 = txnPoolNodeSet[0]
    rep1 = node1.replicas[0]
    _, stableChk = rep1.firstCheckPoint
    oldChkpointMsg = Checkpoint(rep1.instId, rep1.viewNo, *_, stableChk.digest)
    rep1.send(oldChkpointMsg)
    recvReplicas = [n.replicas[0] for n in txnPoolNodeSet[1:]]
    looper.run(eventually(checkDiscardMsg, recvReplicas, oldChkpointMsg, "Checkpoint already stable", retryWait=1))
