import sys
import pytest
from commute_tube.__main__ import main, CommuteTube
from _pytest.monkeypatch import MonkeyPatch
import json
import os
import youtube_dl
import subprocess
import random
import string
from urllib.parse import urlparse

# Strategy
# 1. Write config to temp file
# 2. Start main with temp file as argument
# 3. Check if mock has been called
# 4. Check if files are in stdout

base_download_folder = "Download"



monkeypatch = MonkeyPatch()

def init_commute_tube(tmpdir, config, additional_args, to_be_downloaded_urls, expected_return_code=0):
    downloaded_urls = []

    params = []

    def mockdownload(ytdl, source):
        logger = ytdl.params['logger']
        logger.debug("[Mockdownload] Passed parameters: %s" % ytdl.params)

        # Extract the submitted information for later processing
        downloaded_urls.append(source[0])
        params.append(ytdl.params)

        # Fake a downloaded file to destination
        fake_filename = urlparse(source[0]).hostname + ".mp4"
        download_path = ytdl.params['outtmpl'].split("%")[0]
        file = open(download_path + fake_filename, "w") 

        # Generate random 200 byte content
        file.write(''.join([random.choice(string.ascii_letters + string.digits) for n in range(200)])) 

    monkeypatch.setattr(youtube_dl.YoutubeDL, 'download', mockdownload)
    monkeypatch.setattr(youtube_dl, 'version', "ct_test_mock")

    p = tmpdir.mkdir("commuteconfig").join("config.json")
    p.write(config)

    temp_conf_file = p.strpath

    sys.argv = [
        "commute-tube",
        "--config",
        temp_conf_file
    ]

    sys.argv.extend(additional_args)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == expected_return_code 

    assert downloaded_urls == to_be_downloaded_urls

    return params

def build_config(tmpdir, body, mount_and_unmount=False):
    p = tmpdir.mkdir("penpath")
    pen_path = p.strpath 

    base_config_header = """{
    "pen" : {
        "penPath" : "%s",
        "mountAndUnmount" : "%s",
        "downloadFolder" : "%s",
        "common" : {
            "writesubtitles" : true,
            "format" : "quality_setting_from_common"
            }
    },
    "source" : [
    """ % (pen_path, mount_and_unmount, base_download_folder)

    base_config_footer = """    ]
    }"""
    return base_config_header + body + base_config_footer, pen_path


def test_run_basic_setting(tmpdir):

    config, pen_path = build_config(tmpdir, """
            {
                "url" : "https://url1.com",
                "description" : "Url 1",
                "playlistend" : 3
            },
            {
                "url" : "https://url2.com",
                "description" : "Url 2",
                "playlistend" : 3,
                "format" : "quality_setting_from_source"
            },
            {
                "url" : "https://url3.com",
                "description" : "Url 3",
                "outtmpl" : "CUSTOM_OUTTMPL_"
            },
            {
                "url": [
                    "https://multiurl1.com",
                    "https://multiurl2.com"
                    ],
                "description" : "Multi Urls"
            },
            {
                "shellscript" : "printf 'https://url3fromshell.com\\nhttps://url4fromshell.com'",
                "description" : "Shellscript",
                "description" : "Shellscript",
                "playlistend" : 3
            }
    """)

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[],
        to_be_downloaded_urls=[
            "https://url1.com",
            "https://url2.com",
            "https://url3.com",
            "https://multiurl1.com",
            "https://multiurl2.com",
            "https://url3fromshell.com",
            "https://url4fromshell.com"
            ]
    )

    # Check if format has been obtained from common if not set
    assert processed_params[0]["format"] == "quality_setting_from_common" 
    
    # Check if format has been taken from the source if set in the source
    assert processed_params[1]["format"] == "quality_setting_from_source" 

    assert processed_params[2]["outtmpl"].startswith(pen_path + "/" + base_download_folder + "/" + "CUSTOM_OUTTMPL_")

    # Check if output path contains the base path and download folder name from the config
    assert processed_params[0]["outtmpl"].startswith(pen_path + "/" + base_download_folder)
    assert processed_params[1]["outtmpl"].startswith(pen_path + "/" + base_download_folder)

def test_run_file_copy(tmpdir):

    p = tmpdir.mkdir("source").join("testfile.mp4")
    p.write(''.join([random.choice(string.ascii_letters + string.digits) for n in range(200)]))

    src_file_path = p.strpath

    config, pen_path = build_config(tmpdir, """
            {
                "path" : "%s",
                "description" : "Url 1"
            }
    """ % src_file_path)

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[],
        to_be_downloaded_urls=[
            ]
    )

    assert processed_params == []

def test_run_file_copy_but_exists_in_place(tmpdir):

    p = tmpdir.mkdir("source").join("testfile.mp4")
    p.write(''.join([random.choice(string.ascii_letters + string.digits) for n in range(200)]))

    src_file_path = p.strpath

    config, pen_path = build_config(tmpdir, """
            {
                "path" : "%s",
                "description" : "Url 1"
            }
    """ % src_file_path)

    target_folder = pen_path + "/" + base_download_folder
    os.makedirs(target_folder)
    target_file_name =  target_folder + "/testfile.mp4"
    file = open(target_file_name, "w") 

    # Generate random 200 byte content
    file.write(''.join([random.choice(string.ascii_letters + string.digits) for n in range(200)])) 

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[],
        to_be_downloaded_urls=[
            ]
    )

    assert processed_params == []


def test_check_pen_can_be_mounted(tmpdir):

    def mock_check_call(input):
        return True

    def mock_ismount(input):
        return False

    monkeypatch.setattr(subprocess, 'check_call', mock_check_call)
    monkeypatch.setattr(os.path, 'ismount', mock_ismount)

    config, pen_path = build_config(tmpdir, "", mount_and_unmount=True)

    init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
            "--check"
        ],
        to_be_downloaded_urls=[]
        )

def test_check_pen_can_not_be_mounted(tmpdir):

    def mock_check_call(input):
        raise subprocess.CalledProcessError(1, "Mocking error")

    monkeypatch.setattr(subprocess, 'check_call', mock_check_call)
    config, pen_path = build_config(tmpdir, "", mount_and_unmount=True)

    init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
            "--check"
        ],
        to_be_downloaded_urls=[],
        expected_return_code=1
        )
