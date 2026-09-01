#!/usr/bin/env python3
"""V31 custody and statistical contract.

State slice: continual-learning-gemma3-fineweb-edu-replication-v31.
"""

from __future__ import annotations

import contextlib
import ctypes
import hashlib
import json
import math
import os
import shutil
import socket
import stat
import subprocess
import urllib.request
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any, Callable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v31"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV31"
RAW_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1"
)
PRIOR_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1"
)
SOURCE_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v31-source"
)
CORPUS_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v31-corpus"
)
RESULT_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v31-result"
)
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
MODEL_SNAPSHOT_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v31-model-snapshot"
)
PROTOCOL_PATH = (
    REPO_ROOT
    / "docs/research/continual-learning/249-gemma3-fineweb-edu-replication-v31-protocol.md"
)
PACKET_PATH = (
    REPO_ROOT
    / "docs/research/continual-learning/250-gemma3-fineweb-edu-replication-v31-review-packet.md"
)
RECEIPT_PATH = (
    REPO_ROOT
    / "docs/research/continual-learning/251-gemma3-fineweb-edu-replication-v31-independent-review-2026-08-31.json"
)
PROTOCOL_SHA256 = "135a83f1d5639be473ba368af85fcacb7834e07bf66124ff0b6ef5868a1e942a"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-v31-source"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-v31-corpus"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-v31-result"
REVIEW_SCHEMA = "gemma3-fineweb-edu-replication-v31-independent-review"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG, DATASET_SPLIT = "fineweb-edu-crawl-shards", "train"
DATASET_FILES = (
    {
        "crawl": "CC-MAIN-2013-20",
        "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet",
        "byte_len": 2_369_456_837,
        "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03",
    },
    {
        "crawl": "CC-MAIN-2024-10",
        "path": "data/CC-MAIN-2024-10/000_00000.parquet",
        "byte_len": 1_911_528_585,
        "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484",
    },
)
DATASET_BYTE_COUNT = sum(item["byte_len"] for item in DATASET_FILES)
PRIOR_MANIFEST_SHA256 = (
    "9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3"
)
MODEL_STABLE_MANIFEST_SHA256 = (
    "69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256"
)
MODEL_CACHE_MANIFEST_SHA256 = (
    "ba026071c4026cdc5b4692c2d43b3859d1211b97c3c3a5f7cae5cffd058f6485"
)
MODEL_STABLE_FILES = (
    ".gitattributes",
    "README.md",
    "added_tokens.json",
    "config.json",
    "model.safetensors",
    "model.safetensors.index.json",
    "preprocessor_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
)
MODEL_CACHE_FILES = (
    ".cache/huggingface/.gitignore",
    ".cache/huggingface/CACHEDIR.TAG",
    ".cache/huggingface/download/.gitattributes.metadata",
    ".cache/huggingface/download/README.md.metadata",
    ".cache/huggingface/download/added_tokens.json.metadata",
    ".cache/huggingface/download/config.json.metadata",
    ".cache/huggingface/download/model.safetensors.index.json.metadata",
    ".cache/huggingface/download/model.safetensors.metadata",
    ".cache/huggingface/download/preprocessor_config.json.metadata",
    ".cache/huggingface/download/special_tokens_map.json.metadata",
    ".cache/huggingface/download/tokenizer.json.metadata",
    ".cache/huggingface/download/tokenizer.model.metadata",
    ".cache/huggingface/download/tokenizer_config.json.metadata",
)
PRIOR_HISTORY = (
    {
        "path": "docs/research/continual-learning/143-gemma3-fineweb-edu-replication-v1-protocol.md",
        "sha256": "1e42fc79c8486b1534fd2996f58c7a78de93e287249d14b347f013846d2756ff",
    },
    {
        "path": "docs/research/continual-learning/144-gemma3-fineweb-edu-replication-v1-review-packet.md",
        "sha256": "969146684618f7b625cac33e2e6bd38435ed35dcf23ab42d7d53dc65f10e22f8",
    },
    {
        "path": "docs/research/continual-learning/145-gemma3-fineweb-edu-replication-v1-independent-review-rejection-2026-08-30.json",
        "sha256": "126b3cced429d52fda6ec6cee7f63a7b87eb7d897d24f9b286f38de642ab8249",
    },
    {
        "path": "docs/research/continual-learning/146-gemma3-fineweb-edu-replication-v2-protocol.md",
        "sha256": "580d3890668303e870184e910e0c0cd2098ddb6064b89da565385489e7e71564",
    },
    {
        "path": "docs/research/continual-learning/147-gemma3-fineweb-edu-replication-v2-review-packet.md",
        "sha256": "b706f7c699838e22c702e6af0725dfe640fd724d778d09828dd292770f625483",
    },
    {
        "path": "docs/research/continual-learning/148-gemma3-fineweb-edu-replication-v3-protocol.md",
        "sha256": "5c9c8e0b6ede43bde9fa66a98fb515b597fafa2f3ebcd811c1925ca5a457b8f7",
    },
    {
        "path": "docs/research/continual-learning/149-gemma3-fineweb-edu-replication-v3-review-packet.md",
        "sha256": "ce745e40260cc6dce814cbba0d7706c35207c38bc19622186813c4800e7a140b",
    },
    {
        "path": "docs/research/continual-learning/151-gemma3-fineweb-edu-replication-v4-protocol.md",
        "sha256": "b7007d4cdc7e986b01b6b69ac196454d555e2b2704f2a73e1875b317e3751e2e",
    },
    {
        "path": "docs/research/continual-learning/152-gemma3-fineweb-edu-replication-v4-review-packet.md",
        "sha256": "5ea9a8485b18e4107bebb5a53798983628738dd75f5b454b829e41244759347b",
    },
    {
        "path": "docs/research/continual-learning/154-gemma3-fineweb-edu-replication-v5-protocol.md",
        "sha256": "366e2511b65769e904a560bd7db5deddfd102cfa647efa99b89fb03f7293cbef",
    },
    {
        "path": "docs/research/continual-learning/155-gemma3-fineweb-edu-replication-v5-review-packet.md",
        "sha256": "57025b835ae99c739b6a30f66d0106e3549535591f295e0cae8c240f162a22bb",
    },
    {
        "path": "docs/research/continual-learning/157-gemma3-fineweb-edu-replication-v6-protocol.md",
        "sha256": "90fcbd2602ca215f392faa924316a9d5c34ae1ccb504716b00e1f58ed274c507",
    },
    {
        "path": "docs/research/continual-learning/158-gemma3-fineweb-edu-replication-v6-review-packet.md",
        "sha256": "cc5aab926501c3dbd6eccac5a8ba62347a056dc7ec9a2802be5b2c1d948effd7",
    },
    {
        "path": "docs/research/continual-learning/160-gemma3-fineweb-edu-replication-v7-protocol.md",
        "sha256": "f973c8798b9add05c53f0149b47716ee58b8ea232de88d73dd67b6d110b8da08",
    },
    {
        "path": "docs/research/continual-learning/161-gemma3-fineweb-edu-replication-v7-review-packet.md",
        "sha256": "7a5bacf8fb726d1645e7a24b9cda4158d8f0e8b9610a75499e5cbedd08d3bd5d",
    },
    {
        "path": "docs/research/continual-learning/162-gemma3-fineweb-edu-replication-v7-independent-review-2026-08-30.json",
        "sha256": "48ff180efa579bcbcc94562d8569937939dc96962da56b3e291e84fdfa35cee1",
    },
    {
        "path": "docs/research/continual-learning/163-gemma3-fineweb-edu-replication-v8-protocol.md",
        "sha256": "bb700fec755b53cf0470ccefb3dea6fb70f3b9b40c1db9d7a04d0733a2c534ab",
    },
    {
        "path": "docs/research/continual-learning/164-gemma3-fineweb-edu-replication-v8-review-packet.md",
        "sha256": "efe9322e74657c39298f136687b79c56c4d470d47c48e8ac18c5f03d43373ecc",
    },
    {
        "path": "docs/research/continual-learning/165-gemma3-fineweb-edu-replication-v8-independent-review-rejection-2026-08-30.json",
        "sha256": "297ad7e819276034c237cb586969cc5f5ce07920c4c58448868c65159f75c916",
    },
    {
        "path": "docs/research/continual-learning/166-gemma3-fineweb-edu-replication-v9-protocol.md",
        "sha256": "32bcdb5c449453fe311e0fcaccbfa160172360abcae68d533c5e2cabffffb536",
    },
    {
        "path": "docs/research/continual-learning/167-gemma3-fineweb-edu-replication-v9-review-packet.md",
        "sha256": "b5e75229374991ca205a796af6e0f1c7fb061df9176fdad30492a8aa62ef6376",
    },
    {
        "path": "docs/research/continual-learning/168-gemma3-fineweb-edu-replication-v9-independent-review-rejection-2026-08-30.json",
        "sha256": "6ddfd7a1bd323aa7a47cc9269494d4c5abb94d686c74784f0fe6b97a3548587c",
    },
    {
        "path": "docs/research/continual-learning/169-gemma3-fineweb-edu-replication-v10-protocol.md",
        "sha256": "b5652653f04b1970af662cea7cca36ad274f4ffb67c1a840a40b7a249bd35503",
    },
    {
        "path": "docs/research/continual-learning/170-gemma3-fineweb-edu-replication-v10-review-packet.md",
        "sha256": "ffa7d2204757d776bd755475b37e7f67433fb5ccb8a4b1d45b884a13699a8f15",
    },
    {
        "path": "docs/research/continual-learning/171-gemma3-fineweb-edu-replication-v10-independent-review-rejection-2026-08-30.json",
        "sha256": "1282bdf256c7e137d651cf1916e9eaa5f5e088fa4b4620ba5edbecd9dbd002d6",
    },
    {
        "path": "docs/research/continual-learning/172-gemma3-fineweb-edu-replication-v11-protocol.md",
        "sha256": "657c27770ce67279adf1e38737d8dd9970cf5dcd0eb5721f089cac1319c08e07",
    },
    {
        "path": "docs/research/continual-learning/173-gemma3-fineweb-edu-replication-v11-review-packet.md",
        "sha256": "2098477e97f96a27b9d181ecad78058937f88ad424530c26d6709602998e411f",
    },
    {
        "path": "docs/research/continual-learning/174-gemma3-fineweb-edu-replication-v11-independent-review-2026-08-30.json",
        "sha256": "aa2808bf73b7cdd534fa8efb2cf541aca3c89a20b6a6a0809c82395977cca80b",
    },
    {
        "path": "docs/research/continual-learning/175-gemma3-fineweb-edu-replication-v11-execution-failure-2026-08-30.json",
        "sha256": "c4a28b523bee4f320ba06f58cd320b2c68ecd32eaccd425a3e81682eb9bce71f",
    },
    {
        "path": "docs/research/continual-learning/176-gemma3-fineweb-edu-replication-v12-protocol.md",
        "sha256": "08050a2d4b50749a29697d4828bd18907c7f59f9bcf542281e20851dd5327f80",
    },
    {
        "path": "docs/research/continual-learning/177-gemma3-fineweb-edu-replication-v12-review-packet.md",
        "sha256": "6c8fa21d91f9e43e0f43453ef3e5284e06f5c40322459965a18b1beab4925e47",
    },
    {
        "path": "docs/research/continual-learning/178-gemma3-fineweb-edu-replication-v12-independent-review-rejection-2026-08-30.json",
        "sha256": "bcfeac11c316facdfbcf53bbccc646fbfa63b4daf6a359f28de52f9b23ea3201",
    },
    {
        "path": "docs/research/continual-learning/179-gemma3-fineweb-edu-replication-v13-protocol.md",
        "sha256": "a8c98f0bf550d0e3cfddf8cd669643f30c74ef0698246cae3d19624e92d159c4",
    },
    {
        "path": "docs/research/continual-learning/180-gemma3-fineweb-edu-replication-v13-review-packet.md",
        "sha256": "68da8936831ff5f252f92f7538d6b441b9466710725733e873cc897f88943db0",
    },
    {
        "path": "docs/research/continual-learning/181-gemma3-fineweb-edu-replication-v13-independent-review-2026-08-30.json",
        "sha256": "aedc2e8ca7fe757e438c0f678185e2c3113033103c6a314e4682bac0a1300045",
    },
    {
        "path": "docs/research/continual-learning/182-gemma3-fineweb-edu-replication-v13-execution-failure-2026-08-30.json",
        "sha256": "006c05bdb13084dd176d7200177dd2b99c8f40d1d6a76061715012cfa868165f",
    },
    {
        "path": "docs/research/continual-learning/183-gemma3-fineweb-edu-replication-v14-protocol.md",
        "sha256": "80c1e441359eb28e16b5b2208a7976cbe9ad9c23448c90f4c6ee2fbaa6d9d4ec",
    },
    {
        "path": "docs/research/continual-learning/184-gemma3-fineweb-edu-replication-v14-review-packet.md",
        "sha256": "2a4b0d2efb50a4812c67c2e1c00d0e6457b38a08d3fa42a941ce7fbeef8c8670",
    },
    {
        "path": "docs/research/continual-learning/185-gemma3-fineweb-edu-replication-v14-independent-review-2026-08-30.json",
        "sha256": "c9dd921736e6ca2fe24592e92718aae5405be0a735adb28f635c08f0c6a947ff",
    },
    {
        "path": "docs/research/continual-learning/186-gemma3-fineweb-edu-replication-v14-execution-failure-2026-08-30.json",
        "sha256": "7348e2fe69779b90f6ba27e875463aa55f1e234880112e96a1f44e724a1c082c",
    },
    {
        "path": "docs/research/continual-learning/187-gemma3-fineweb-edu-replication-v15-protocol.md",
        "sha256": "087ef49c12c06428bc992ed8b48145cd3bae2a12898ca66d108ef7d65c6bb4d3",
    },
    {
        "path": "docs/research/continual-learning/188-gemma3-fineweb-edu-replication-v15-review-packet.md",
        "sha256": "2a1206f286b4eb08b8e5495199ef720455f83457e7900569dfa45c488e492637",
    },
    {
        "path": "docs/research/continual-learning/189-gemma3-fineweb-edu-replication-v15-independent-review-rejection-2026-08-31.json",
        "sha256": "ecb83dd8ba2c0445d12bab6d3175706eb38c2cc0fd01ad6ef615a5a9fdc45682",
    },
    {
        "path": "docs/research/continual-learning/190-gemma3-fineweb-edu-replication-v16-protocol.md",
        "sha256": "311697866fb9243b8a85b0ec51327b457d10b8624c4110ce772bdbf66b30804c",
    },
    {
        "path": "docs/research/continual-learning/191-gemma3-fineweb-edu-replication-v16-review-packet.md",
        "sha256": "76ee951c895c7faf6d1fa01771350aee1c0b5d78dd4094b1e1ada63dc41f95d1",
    },
    {
        "path": "docs/research/continual-learning/192-gemma3-fineweb-edu-replication-v16-independent-review-rejection-2026-08-31.json",
        "sha256": "b93251b33ab80c3ab1183f0b8a56409e804a2973932aee879f6dc93aa0a4cc52",
    },
    {
        "path": "docs/research/continual-learning/193-gemma3-fineweb-edu-replication-v17-protocol.md",
        "sha256": "c5279ff97371aa8441b92eb39f19022cfc7b48c1d9b91ce761224060b63b0334",
    },
    {
        "path": "docs/research/continual-learning/194-gemma3-fineweb-edu-replication-v17-review-packet.md",
        "sha256": "bda9a0812b0a42f7f759f13363015a1e492d5522f0ffbda0404abef1f271a23f",
    },
    {
        "path": "docs/research/continual-learning/196-gemma3-fineweb-edu-replication-v17-independent-review-rejection-2026-08-31.json",
        "sha256": "4a0f4dbb847329ebba4ae4ea346f5938cff2b199c7841b5b6401946ab1995163",
    },
    {
        "path": "docs/research/continual-learning/197-gemma3-fineweb-edu-replication-v18-protocol.md",
        "sha256": "9d345f2a07f276de51930d5cb90ce56aa31610fc993140f1194aaf91fa10b290",
    },
    {
        "path": "docs/research/continual-learning/198-gemma3-fineweb-edu-replication-v18-review-packet.md",
        "sha256": "72cbd60931b6a007912505a0c0ce7112e503977864fce83dc6868a20fe3eaab6",
    },
    {
        "path": "docs/research/continual-learning/200-gemma3-fineweb-edu-replication-v18-independent-review-rejection-2026-08-31.json",
        "sha256": "fdcdbf7ac4842b565992bf090f96eaef3bc892918a260936c578083769f1d28f",
    },
    {
        "path": "docs/research/continual-learning/201-gemma3-fineweb-edu-replication-v19-protocol.md",
        "sha256": "dfb5de0834a656fb07cebbad7dfb47aa26473cfada3da793ee4b4ff3314dd442",
    },
    {
        "path": "docs/research/continual-learning/202-gemma3-fineweb-edu-replication-v19-review-packet.md",
        "sha256": "b86d24b26e0bd127f81ba5834674e41ba8091a70f87d5a8c87c98198e32bd6c1",
    },
    {
        "path": "docs/research/continual-learning/204-gemma3-fineweb-edu-replication-v19-independent-review-rejection-2026-08-31.json",
        "sha256": "6456f3be5db46ebe96c91d56f5bfe3de543e2afb3a6d344737c9cf52f176ea00",
    },
    {
        "path": "docs/research/continual-learning/205-gemma3-fineweb-edu-replication-v20-protocol.md",
        "sha256": "f42080f8ac660c175941f92cc18ecfd9d736e0afc77f7cc9b40cd4926538a0f2",
    },
    {
        "path": "docs/research/continual-learning/206-gemma3-fineweb-edu-replication-v20-review-packet.md",
        "sha256": "bb5438bb22468c58ddfad471ef9a9f422b6d0cdb95e8aa06f922857e26cea6e5",
    },
    {
        "path": "docs/research/continual-learning/208-gemma3-fineweb-edu-replication-v20-independent-review-rejection-2026-08-31.json",
        "sha256": "f0efd7cf10419ba4ab2fdeab52c197cca81751011e8d63a5049a7f4021e01d8b",
    },
    {
        "path": "docs/research/continual-learning/209-gemma3-fineweb-edu-replication-v21-protocol.md",
        "sha256": "968c11659184a6b0517cbfbd412c228b6e3d0113594ac17b6f34e2cb5e0ff255",
    },
    {
        "path": "docs/research/continual-learning/210-gemma3-fineweb-edu-replication-v21-review-packet.md",
        "sha256": "d47e9edad6965504b3775f9bf10b96a5f1296bfa09a2310affbeb17552c46cbc",
    },
    {
        "path": "docs/research/continual-learning/212-gemma3-fineweb-edu-replication-v21-independent-review-rejection-2026-08-31.json",
        "sha256": "270692bbd0e97cfdd8a76c9195d2c16f7b3a2452b932355ff974447e78a283a9",
    },
    {
        "path": "docs/research/continual-learning/213-gemma3-fineweb-edu-replication-v22-protocol.md",
        "sha256": "d52a99e412a95b2e8c88fd118fab75ff4262db1db1cef274ccb8c1402e52c0e3",
    },
    {
        "path": "docs/research/continual-learning/214-gemma3-fineweb-edu-replication-v22-review-packet.md",
        "sha256": "ec8f8c264b7cc2e056ed8ec27de38a271b6d5007917ccd441454f0e1c34e95b6",
    },
    {
        "path": "docs/research/continual-learning/216-gemma3-fineweb-edu-replication-v22-independent-review-rejection-2026-08-31.json",
        "sha256": "a2d514e79d58e1a3cac30a9046456fa62384ac5c200b9a4a6d3bb534dac4563b",
    },
    {
        "path": "docs/research/continual-learning/217-gemma3-fineweb-edu-replication-v23-protocol.md",
        "sha256": "71a71706fe0be7c7f099b2b5fc84ed8c5269164cee3306dadd234ff1e86caaff",
    },
    {
        "path": "docs/research/continual-learning/218-gemma3-fineweb-edu-replication-v23-review-packet.md",
        "sha256": "e52f606e88f2c8626e2e9a4c681838ea63c341584bee4188bb3221694b630344",
    },
    {
        "path": "docs/research/continual-learning/220-gemma3-fineweb-edu-replication-v23-independent-review-rejection-2026-08-31.json",
        "sha256": "a8bb97c68986081c432816309d3a4c0ccfbf67bccc53e192e0960437fbcfcd01",
    },
    {
        "path": "docs/research/continual-learning/221-gemma3-fineweb-edu-replication-v24-protocol.md",
        "sha256": "02d65b554c62650ed3bc2ab07e33c07ec994451ce67f768bb0684281db188178",
    },
    {
        "path": "docs/research/continual-learning/222-gemma3-fineweb-edu-replication-v24-review-packet.md",
        "sha256": "03d7b72e3114eb0d43aaf05c6680467b02305193f01796408f6743d1bfbd7c67",
    },
    {
        "path": "docs/research/continual-learning/224-gemma3-fineweb-edu-replication-v24-independent-review-rejection-2026-08-31.json",
        "sha256": "4bf1fe9792821ef903fa0729b82442fd2882988934685391e303668b17b038ad",
    },
    {
        "path": "docs/research/continual-learning/225-gemma3-fineweb-edu-replication-v25-protocol.md",
        "sha256": "47fa38a2002ba9635de5c9f7a9849e273d1fa5bd8e77721770275a1761046f54",
    },
    {
        "path": "docs/research/continual-learning/226-gemma3-fineweb-edu-replication-v25-review-packet.md",
        "sha256": "8bbcc05230f5105c77147d088bc8191b2ead9d139f9a9230225c93e7803d8661",
    },
    {
        "path": "docs/research/continual-learning/228-gemma3-fineweb-edu-replication-v25-independent-review-rejection-2026-08-31.json",
        "sha256": "93dd96ae0dc39f52432edf8136a39db770434c861b196e5549f5adcb662fbcd7",
    },
    {
        "path": "docs/research/continual-learning/229-gemma3-fineweb-edu-replication-v26-protocol.md",
        "sha256": "c87c75042b866e5777cf0077d0bbf6201c4ba9838e565816a474de0a79843316",
    },
    {
        "path": "docs/research/continual-learning/230-gemma3-fineweb-edu-replication-v26-review-packet.md",
        "sha256": "905f3a3c82b21ddf2d5bc32d134150d3e52f34bba18e4c99a2c7edcd9446fbbe",
    },
    {
        "path": "docs/research/continual-learning/232-gemma3-fineweb-edu-replication-v26-independent-review-rejection-2026-08-31.json",
        "sha256": "a3937e52bac02eaf50a4b10facec1c8b191baeac90b34fcc6baa4916c31af193",
    },
    {
        "path": "docs/research/continual-learning/233-gemma3-fineweb-edu-replication-v27-protocol.md",
        "sha256": "966ad4a195f675dfb54e72331e6a5fe3c06ba1b7ad7753000795f94fd7740171",
    },
    {
        "path": "docs/research/continual-learning/234-gemma3-fineweb-edu-replication-v27-review-packet.md",
        "sha256": "f32901d0f92a775f0207bb33dacbf703143527e228d8ad265e64efb6e41306fd",
    },
    {
        "path": "docs/research/continual-learning/236-gemma3-fineweb-edu-replication-v27-independent-review-rejection-2026-08-31.json",
        "sha256": "9578e02c5e4f7857a6d593bb54c015ef0fbfec31b9d995f554f00b3c9368cc9f",
    },
    {
        "path": "docs/research/continual-learning/237-gemma3-fineweb-edu-replication-v28-protocol.md",
        "sha256": "d9c77afb6f10eed7a6a6bbd51a46d7412e3b221cf8472940ab00c531de2b9a60",
    },
    {
        "path": "docs/research/continual-learning/238-gemma3-fineweb-edu-replication-v28-review-packet.md",
        "sha256": "3494720563de895acbfdeec3d2da821cb4b1d78652b09bec58a249ab45941384",
    },
    {
        "path": "docs/research/continual-learning/240-gemma3-fineweb-edu-replication-v28-independent-review-rejection-2026-08-31.json",
        "sha256": "dec362983cfc11d508215d98a5649934039004c86fae52add5037802849361ad",
    },
    {
        "path": "docs/research/continual-learning/241-gemma3-fineweb-edu-replication-v29-protocol.md",
        "sha256": "cdf88630165496c98d9d97aad17509c0d1b92d174135adbe17827b67971bc283",
    },
    {
        "path": "docs/research/continual-learning/242-gemma3-fineweb-edu-replication-v29-review-packet.md",
        "sha256": "5c7351268114c9b211f6087746ab23394f6e7de3ad6fa7fbd502a7edc5486ee0",
    },
    {
        "path": "docs/research/continual-learning/244-gemma3-fineweb-edu-replication-v29-independent-review-rejection-2026-08-31.json",
        "sha256": "92bc33c3e2742a3b9e5cc23b0c127ef899e78e77f7153fc4e2a280ed145608f8",
    },
    {
        "path": "docs/research/continual-learning/245-gemma3-fineweb-edu-replication-v30-protocol.md",
        "sha256": "9dfc3f54aa9458e7962881ce5594aa6050359b81a75ec9bd463213e912d81f8c",
    },
    {
        "path": "docs/research/continual-learning/246-gemma3-fineweb-edu-replication-v30-review-packet.md",
        "sha256": "52869a726047672d26e0c6d12a9c03d6ae7cb13e62f0af2a6980f7aed5e49f89",
    },
    {
        "path": "docs/research/continual-learning/248-gemma3-fineweb-edu-replication-v30-independent-review-invalidated-2026-08-31.json",
        "sha256": "c838b97c6393bfaf6e21c4bade2b3354cbd6487e32e3c218e738b69fa652d73b",
    },
)
HISTORICAL_ABSENT_RECEIPT_PATTERNS = (
    "docs/research/continual-learning/*gemma3-fineweb-edu-replication-v2-independent-review*.json",
    "docs/research/continual-learning/*gemma3-fineweb-edu-replication-v3-independent-review*.json",
    "docs/research/continual-learning/*gemma3-fineweb-edu-replication-v4-independent-review*.json",
    "docs/research/continual-learning/*gemma3-fineweb-edu-replication-v5-independent-review*.json",
    "docs/research/continual-learning/*gemma3-fineweb-edu-replication-v6-independent-review*.json",
)


def validate_history_absences() -> list[str]:
    present = [
        pattern
        for pattern in HISTORICAL_ABSENT_RECEIPT_PATTERNS
        if any(REPO_ROOT.glob(pattern))
    ]
    if present:
        raise ValueError(f"undocumented historical receipt appeared: {present}")
    return present

RUNTIME_VERSIONS = {"mlx": "0.31.2", "mlx-lm": "0.31.3", "pyarrow": "24.0.0"}
FRESH_ROW_START, FRESH_ROW_COUNT, WINDOW_TOKENS = 18_432, 16_384, 1_024
FRESH_ROW_END = FRESH_ROW_START + FRESH_ROW_COUNT
FIT_WINDOW_COUNT = ASSESSMENT_WINDOW_COUNT = 64
FIT_ALPHA, FIT_BETA, EVALUATION_ALPHA, EVALUATION_BETA = 0.10, 0.90, 0.15, 0.85
TEMPERATURE_CONTROL = 1.20
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
EPSILON, PARITY_TOLERANCE = 1e-6, 1e-5
BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, BOOTSTRAP_CONFIDENCE = 10_000, 2_026_0829, 0.95
CONTROL_NAMES = (
    "native_baseline",
    "zero_alpha_identity",
    "all_candidate_evaluations",
    "temperature_1.20_baseline",
    "temperature_1.20_intervention",
    "deterministic_repeat",
    "frozen_model_manifest",
    "frozen_model_parameters",
)
REVIEW_FINDINGS = (
    "custody_exact_pinned_data_identity",
    "fit_assessment_prior_pilot_disjointness",
    "locked_configuration_and_paper_target_treatment",
    "controls_and_frozen_weight_behavior",
    "exact_bootstrap_and_uncertainty_rule",
    "aggregate_per_document_retention_and_validator_behavior",
    "v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced",
)
IMPLEMENTATION_FILES = (
    PROTOCOL_PATH,
    PACKET_PATH,
    REPO_ROOT
    / "experiments/continual_learning/gemma3_fineweb_edu_replication_v31_contract.py",
    REPO_ROOT
    / "experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v31.py",
    REPO_ROOT
    / "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v31.py",
    REPO_ROOT
    / "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v31.py",
    REPO_ROOT
    / "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v31.py",
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validation_binding(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("validation binding requires an object")
    return {key: item for key, item in value.items() if key != "result_snapshot"}


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with stable_binary_file(path, "hashed file") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def reject_symlink_components(path: Path, label: str) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError(f"{label} contains symlink component: {current}")


def exact_path(path: Path, expected: Path, label: str) -> Path:
    supplied = path.expanduser().absolute()
    if supplied != expected:
        raise ValueError(f"{label} must equal {expected}: {supplied}")
    reject_symlink_components(supplied, label)
    return supplied


def exact_or_staging(path: Path, expected: Path, label: str) -> Path:
    supplied = path.expanduser().absolute()
    if supplied != expected and (
        supplied.parent != expected.parent
        or not supplied.name.startswith(f".{expected.name}.staging-")
    ):
        raise ValueError(f"{label} is not the V31 root or staging sibling")
    reject_symlink_components(supplied, label)
    return supplied


def regular(path: Path, label: str) -> Path:
    reject_symlink_components(path.absolute(), label)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def stable_read_bytes(path: Path, label: str) -> bytes:
    checked = regular(path, label)
    before_path = checked.stat()
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(checked, flags)
    chunks: list[bytes] = []
    try:
        before_fd = os.fstat(descriptor)
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = checked.stat()
    signatures = (
        (before_path.st_dev, before_path.st_ino, before_path.st_size, before_path.st_mtime_ns),
        (before_fd.st_dev, before_fd.st_ino, before_fd.st_size, before_fd.st_mtime_ns),
        (after_fd.st_dev, after_fd.st_ino, after_fd.st_size, after_fd.st_mtime_ns),
        (after_path.st_dev, after_path.st_ino, after_path.st_size, after_path.st_mtime_ns),
    )
    if not (signatures[0] == signatures[1] == signatures[2] == signatures[3]):
        raise RuntimeError(f"{label} changed during read: {checked}")
    return b"".join(chunks)


def _stat_signature(value: os.stat_result) -> tuple[int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


@contextlib.contextmanager
def stable_binary_file(path: Path, label: str) -> Iterator[Any]:
    """Yield one descriptor-backed binary read and reject path replacement."""
    checked = regular(path, label)
    before_path = checked.stat()
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(checked, flags)
    before_fd: os.stat_result | None = None
    after_fd: os.stat_result | None = None
    try:
        before_fd = os.fstat(descriptor)
        if _stat_signature(before_path) != _stat_signature(before_fd):
            raise RuntimeError(f"{label} replaced before read: {checked}")
        handle = os.fdopen(descriptor, "rb", closefd=False)
        try:
            yield handle
        finally:
            handle.close()
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = checked.stat()
    if before_fd is None or after_fd is None:
        raise RuntimeError(f"{label} did not complete descriptor read: {checked}")
    signatures = tuple(
        _stat_signature(item)
        for item in (before_path, before_fd, after_fd, after_path)
    )
    if not (signatures[0] == signatures[1] == signatures[2] == signatures[3]):
        raise RuntimeError(f"{label} changed during read: {checked}")


def safe_relative(root: Path, relative: Any, label: str) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise ValueError(f"{label} must be safe relative")
    candidate = root / relative
    reject_symlink_components(candidate.absolute(), label)
    resolved = candidate.absolute()
    root_abs = root.absolute()
    if resolved == root_abs or root_abs not in resolved.parents:
        raise ValueError(f"{label} escapes root")
    return regular(resolved, label)


def exact_file_set(root: Path, expected: set[str], label: str) -> None:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"{label} must be a real directory")
    reject_symlink_components(root.absolute(), label)
    actual = set()
    allowed_dirs = {
        parent.as_posix()
        for item in expected
        for parent in Path(item).parents
        if parent != Path(".")
    }
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"{label} contains symlink")
        relative = candidate.relative_to(root).as_posix()
        if candidate.is_file():
            actual.add(relative)
        elif not candidate.is_dir() or relative not in allowed_dirs:
            raise ValueError(f"{label} contains unsupported entry: {relative}")
    if actual != expected:
        raise ValueError(f"{label} exact file set mismatch")


def model_manifest_at(
    root: Path,
    label: str,
    model_name: str | None = None,
    require_read_only: bool = False,
) -> dict[str, Any]:
    root = root.absolute()
    if not root.is_dir():
        raise ValueError(f"{label} must be a directory")
    reject_symlink_components(root, label)
    expected = set(MODEL_STABLE_FILES) | set(MODEL_CACHE_FILES)
    exact_file_set(root, expected, label)
    if require_read_only:
        _require_read_only_snapshot(root, label)

    def file_list(names: tuple[str, ...]) -> list[dict[str, Any]]:
        return [
            {
                "path": name,
                "byte_len": (root / name).stat().st_size,
                "sha256": sha256_file(root / name),
            }
            for name in names
        ]

    stable, cache = (
        {
            "model_name": model_name or root.name,
            "files": file_list(MODEL_STABLE_FILES),
        },
        {
            "model_name": model_name or root.name,
            "files": file_list(MODEL_CACHE_FILES),
        },
    )
    return {
        "manifest": stable,
        "manifest_sha256": digest(stable),
        "cache_manifest": cache,
        "cache_manifest_sha256": digest(cache),
    }


def model_manifest(model_path: Path) -> dict[str, Any]:
    root = exact_path(model_path, MODEL_PATH, "model path")
    return model_manifest_at(root, "model tree", MODEL_PATH.name)


def _require_read_only_snapshot(root: Path, label: str) -> None:
    if stat.S_IMODE(root.stat().st_mode) != 0o555:
        raise ValueError(f"{label} root is not read-only")
    for candidate in root.rglob("*"):
        mode = stat.S_IMODE(candidate.stat().st_mode)
        expected = 0o555 if candidate.is_dir() else 0o444
        if mode != expected:
            raise ValueError(f"{label} permissions are not frozen: {candidate}")


def _remove_tree(path: Path, label: str) -> None:
    """Restore deletion permissions before removing a failed snapshot tree."""
    if path.is_symlink():
        path.unlink()
        return
    if not path.exists():
        return
    if not path.is_dir():
        path.unlink()
        return
    for candidate in path.rglob("*"):
        if candidate.is_symlink():
            candidate.unlink()
        elif candidate.is_dir():
            os.chmod(candidate, 0o755)
        else:
            os.chmod(candidate, 0o644)
    os.chmod(path, 0o755)
    shutil.rmtree(path)
    if path.exists() or path.is_symlink():
        raise RuntimeError(f"{label} cleanup did not remove tree: {path}")


def materialize_model_snapshot(model_path: Path) -> Path:
    """Copy the canonical model through stable descriptors before loading."""
    source_root = exact_path(model_path, MODEL_PATH, "model path")
    source_manifest = model_manifest(source_root)
    snapshot = MODEL_SNAPSHOT_ROOT.absolute()
    if snapshot.exists() or snapshot.is_symlink():
        if (
            snapshot.is_symlink()
            or model_manifest_at(
                snapshot,
                "V31 model snapshot",
                MODEL_PATH.name,
                require_read_only=True,
            )
            != source_manifest
        ):
            raise ValueError("V31 model snapshot already exists with a different identity")
        _require_read_only_snapshot(snapshot, "V31 model snapshot")
        return snapshot
    reject_symlink_components(snapshot, "V31 model snapshot")
    staging = snapshot.parent / f".{snapshot.name}.staging-{os.getpid()}"
    if staging.exists() or staging.is_symlink():
        raise FileExistsError(f"V31 model snapshot staging exists: {staging}")
    staging.mkdir()
    published = False
    try:
        expected = tuple(sorted(set(MODEL_STABLE_FILES) | set(MODEL_CACHE_FILES)))
        for relative in expected:
            source = source_root / relative
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with stable_binary_file(source, "V31 model source") as source_handle:
                with destination.open("xb") as destination_handle:
                    shutil.copyfileobj(source_handle, destination_handle, 1024 * 1024)
                    destination_handle.flush()
                    os.fsync(destination_handle.fileno())
            os.chmod(destination, 0o444)
        staged_manifest = model_manifest_at(
            staging, "V31 model snapshot", MODEL_PATH.name
        )
        if staged_manifest != source_manifest:
            raise RuntimeError("V31 model snapshot digest mismatch")
        for directory in sorted(
            (item for item in staging.rglob("*") if item.is_dir()),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            os.chmod(directory, 0o555)
        os.chmod(staging, 0o555)
        os.rename(staging, snapshot)
        published = True
        if (
            model_manifest_at(
                snapshot,
                "V31 model snapshot",
                MODEL_PATH.name,
                require_read_only=True,
            )
            != source_manifest
        ):
            raise RuntimeError("V31 published model snapshot mismatch")
        return snapshot
    except Exception:
        if published and snapshot.exists():
            _remove_tree(snapshot, "V31 published model snapshot")
        if staging.exists():
            _remove_tree(staging, "V31 model snapshot staging")
        raise


def validate_prior_history() -> list[dict[str, str]]:
    validate_history_absences()
    result = []
    for item in PRIOR_HISTORY:
        path = REPO_ROOT / item["path"]
        regular(path, "prior rejection history")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"prior history changed: {item['path']}")
        result.append(dict(item))
    return result


def native_network_denied() -> bool:
    if os.sys.platform != "darwin":
        return False
    try:
        check = ctypes.CDLL(None).sandbox_check
        check.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        check.restype = ctypes.c_int
        return check(os.getpid(), b"network-outbound", 0) == 1
    except (AttributeError, OSError):
        return False


def require_native_network_denial() -> None:
    if not native_network_denied():
        raise RuntimeError("V31 native outbound network denial is not proven")


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    old_env = {
        key: os.environ.get(key)
        for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")
    }
    for key in old_env:
        os.environ[key] = "1"

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("V31 network/process escape denied")

    original_socket = socket.socket
    original_socket_functions = {
        name: getattr(socket, name)
        for name in (
            "create_connection",
            "getaddrinfo",
            "gethostbyname",
            "gethostbyname_ex",
            "gethostbyaddr",
            "getnameinfo",
            "getfqdn",
        )
    }
    original_urlopen = urllib.request.urlopen
    original_subprocess = {
        name: getattr(subprocess, name)
        for name in ("Popen", "run", "check_call", "check_output")
    }
    original_os = {name: getattr(os, name) for name in ("system", "popen")}
    process_names = tuple(
        name
        for name in dir(os)
        if (
            name.startswith("exec")
            or name.startswith("spawn")
            or name in ("posix_spawn", "posix_spawnp", "fork", "forkpty", "startfile")
        )
        and callable(getattr(os, name, None))
    )
    original_process = {name: getattr(os, name, None) for name in process_names}

    class OfflineSocket(original_socket):
        connect = forbidden
        connect_ex = forbidden
        sendto = forbidden
        send = forbidden
        sendall = forbidden
        sendmsg = forbidden
        sendfile = forbidden

    socket.socket = OfflineSocket
    for name in original_socket_functions:
        setattr(socket, name, forbidden)
    urllib.request.urlopen = forbidden
    for name in original_subprocess:
        setattr(subprocess, name, forbidden)
    for name in original_os:
        setattr(os, name, forbidden)
    for name, value in original_process.items():
        if value is not None:
            setattr(os, name, forbidden)
    try:
        yield
    finally:
        socket.socket = original_socket
        for name, value in original_socket_functions.items():
            setattr(socket, name, value)
        urllib.request.urlopen = original_urlopen
        for name, value in original_subprocess.items():
            setattr(subprocess, name, value)
        for name, value in original_os.items():
            setattr(os, name, value)
        for name, value in original_process.items():
            if value is not None:
                setattr(os, name, value)
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def model_parameter_digest(model: Any) -> str:
    import numpy as np
    import mlx.core as mx

    root = model.parameters() if hasattr(model, "parameters") else None
    if root is None:
        raise ValueError("model exposes no parameters")
    hasher = hashlib.sha256()

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                visit(value[key], f"{path}/{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, f"{path}/{index}")
        elif hasattr(value, "shape"):
            mx.eval(value)
            source_dtype = str(value.dtype)
            if source_dtype.endswith("bfloat16"):
                canonical = value.astype(mx.float32)
                mx.eval(canonical)
                array = np.array(canonical)
            else:
                array = np.asarray(value)
            hasher.update(path.encode())
            hasher.update(str(array.shape).encode())
            hasher.update(source_dtype.encode())
            hasher.update(str(array.dtype).encode())
            hasher.update(array.tobytes(order="C"))
        else:
            raise ValueError(f"unsupported parameter at {path}")

    visit(root, "root")
    return hasher.hexdigest()


def bootstrap_mean_ci(deltas: list[float]) -> dict[str, Any]:
    if not deltas:
        raise ValueError("bootstrap requires data")
    values = []
    for value in deltas:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError("bootstrap input must be finite non-boolean")
        values.append(float(value))
    n, samples = len(values), []
    for resample in range(BOOTSTRAP_RESAMPLES):
        total = 0.0
        for position in range(n):
            counter = f"{BOOTSTRAP_SEED}:{resample}:{position}".encode()
            total += values[
                int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % n
            ]
        samples.append(total / n)
    samples.sort()

    def rank(q: float) -> float:
        return samples[
            max(1, min(BOOTSTRAP_RESAMPLES, math.ceil(q * BOOTSTRAP_RESAMPLES))) - 1
        ]

    mean = sum(values) / n
    if not math.isfinite(mean):
        raise ValueError("bootstrap mean is nonfinite")
    return {
        "mean_delta": mean,
        "lower": rank(0.025),
        "upper": rank(0.975),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "confidence": BOOTSTRAP_CONFIDENCE,
        "prng": "sha256-counter-v1",
        "statistic": "mean paired per-document NLL delta selected_minus_baseline",
        "percentile": "nearest-rank-1-indexed",
        "nonfinite": "reject",
    }


def decide_replication(value: dict[str, Any]) -> str:
    mean, upper = value.get("mean_delta"), value.get("upper")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(float(item))
        for item in (mean, upper)
    ):
        raise ValueError("decision values invalid")
    return "ReplicationCandidate" if mean < 0 and upper < 0 else "NoCandidate"


def implementation_manifest() -> dict[str, Any]:
    files = []
    for path in IMPLEMENTATION_FILES:
        reject_symlink_components(path.absolute(), "V31 implementation file")
        item = regular(path, "V31 implementation file")
        files.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "byte_len": item.stat().st_size,
                "sha256": sha256_file(item),
            }
        )
    body = {"state_slice": STATE_SLICE, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def review_file_list() -> list[str]:
    return [path.relative_to(REPO_ROOT).as_posix() for path in IMPLEMENTATION_FILES]


def validate_review_receipt(path: Path) -> dict[str, Any]:
    path = exact_path(path, RECEIPT_PATH, "V31 review receipt")
    value = json.loads(
        stable_read_bytes(path, "V31 review receipt").decode("utf-8")
    )
    if not isinstance(value, dict):
        raise ValueError("V31 review receipt must be an object")
    stored = value.get("receipt_sha256")
    if (
        not isinstance(stored, str)
        or digest({key: item for key, item in value.items() if key != "receipt_sha256"})
        != stored
    ):
        raise ValueError("V31 review receipt self-digest mismatch")
    timestamp = value.get("reviewed_at_utc")
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("V31 review timestamp missing")
    parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    if parsed.microsecond or timestamp != parsed.strftime("%Y-%m-%dT%H:%M:%SZ"):
        raise ValueError("V31 review timestamp noncanonical")
    if (
        value.get("schema") != REVIEW_SCHEMA
        or not isinstance(value.get("reviewer"), str)
        or not value["reviewer"].strip()
        or value.get("review_decision") != "ACCEPT"
        or value.get("effects_run") is not False
        or value.get("state_slice") != STATE_SLICE
        or value.get("protocol_sha256") != sha256_file(PROTOCOL_PATH)
        or value.get("protocol_sha256") != PROTOCOL_SHA256
        or value.get("review_packet_sha256") != sha256_file(PACKET_PATH)
        or value.get("implementation_manifest_sha256")
        != implementation_manifest()["manifest_sha256"]
        or value.get("reviewed_files") != review_file_list()
    ):
        raise ValueError("V31 review receipt binding mismatch")
    expected_keys = {
        "schema",
        "state_slice",
        "reviewer",
        "reviewed_at_utc",
        "effects_run",
        "protocol_sha256",
        "review_packet_sha256",
        "implementation_manifest_sha256",
        "reviewed_files",
        "findings",
        "material_findings",
        "review_decision",
        "receipt_sha256",
    }
    if set(value) != expected_keys:
        raise ValueError("V31 review receipt schema is not closed")
    if type(value.get("effects_run")) is not bool or value["effects_run"] is not False:
        raise ValueError("V31 review effects_run must be a boolean false")
    expected_findings = {name: True for name in REVIEW_FINDINGS}
    findings = value.get("findings")
    if (
        not isinstance(findings, dict)
        or set(findings) != set(expected_findings)
        or any(type(findings[name]) is not bool or findings[name] is not True for name in REVIEW_FINDINGS)
    ):
        raise ValueError("V31 receipt requires seven explicit true findings")
    if value.get("material_findings") != []:
        raise ValueError("V31 ACCEPT receipt must have an empty material_findings list")
    return value


def snapshot_files(root: Path, expected: set[str], label: str) -> list[dict[str, Any]]:
    exact_file_set(root, expected, label)
    result = []
    for relative in sorted(expected):
        path = safe_relative(root, relative, f"{label} file")
        result.append(
            {
                "path": relative,
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return result


def snapshot_code() -> dict[str, Any]:
    return {
        "protocol": stable_read_bytes(PROTOCOL_PATH, "V31 protocol"),
        "packet": stable_read_bytes(PACKET_PATH, "V31 packet"),
        "receipt": stable_read_bytes(RECEIPT_PATH, "V31 receipt"),
        "implementation": implementation_manifest(),
        "history": validate_prior_history(),
    }


def code_snapshot_digest() -> str:
    snapshot = snapshot_code()
    return digest(
        {
            "protocol_sha256": sha256_file(PROTOCOL_PATH),
            "packet_sha256": sha256_file(PACKET_PATH),
            "receipt_sha256": sha256_file(RECEIPT_PATH),
            "implementation_manifest_sha256": snapshot["implementation"]["manifest_sha256"],
            "history": snapshot["history"],
        }
    )

def assert_code_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot_code() != snapshot:
        raise RuntimeError("V31 reviewed bytes or history changed")


def publish_no_replace(
    staging: Path,
    final: Path,
    expected: set[str],
    label: str,
    post_publish_check: Callable[[], None] | None = None,
    expected_snapshot: list[dict[str, Any]] | None = None,
) -> None:
    if final.exists():
        raise FileExistsError(f"{label} final root exists")
    exact_file_set(staging, expected, f"{label} staging")
    before = snapshot_files(staging, expected, f"{label} staging")
    if expected_snapshot is not None and before != expected_snapshot:
        raise RuntimeError(f"{label} publication snapshot mismatch")
    try:
        if expected_snapshot is not None:
            locked_before = snapshot_files(staging, expected, f"{label} staging")
            if locked_before != expected_snapshot:
                raise RuntimeError(f"{label} publication snapshot changed")
            before = locked_before
        os.rename(staging, final)
        if snapshot_files(final, expected, f"{label} final") != before:
            raise RuntimeError(f"{label} publication changed bytes")
        if post_publish_check is not None:
            post_publish_check()
        try:
            after_post_publish = snapshot_files(final, expected, f"{label} final")
        except (RuntimeError, ValueError) as exc:
            raise RuntimeError(f"{label} post-publication bytes changed") from exc
        if after_post_publish != before:
            raise RuntimeError(f"{label} post-publication bytes changed")
    except Exception:
        if final.exists() and not staging.exists():
            os.rename(final, staging)
        raise

def runtime_versions() -> dict[str, str]:
    return {
        name: (version(name) if installed(name) else "unavailable")
        for name in RUNTIME_VERSIONS
    }


def installed(name: str) -> bool:
    try:
        version(name)
    except Exception:
        return False
    return True
