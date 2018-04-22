import sys
import pytest
from commute_tube.__main__ import main
from _pytest.monkeypatch import MonkeyPatch
import os
import youtube_dl
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

        if source[0] == "https://malformedsource.com":
            raise Exception("Provoked Exception")

        # Extract the submitted information for later processing
        downloaded_urls.append(source[0])
        params.append(ytdl.params)

        if not ytdl.params.get("simulate"):

            # Fake a downloaded file to destination
            fake_filename = urlparse(source[0]).hostname + ".mp4"
            download_path = ytdl.params['outtmpl'].split("%")[0]
            file = open(download_path + fake_filename, "w")

            # Generate random 200 byte content
            file.write(''.join([random.choice(string.ascii_letters + string.digits) for n in range(200)]))
        else:
            logger.warn("[Mockdownload] Only debugging since simulate flag is set")

    monkeypatch.setattr(youtube_dl.YoutubeDL, 'download', mockdownload)
    monkeypatch.setattr(youtube_dl, 'version', "ct_test_mock")

    p = tmpdir.mkdir("commuteconfig").join("config.json")
    p.write(config.replace("\n", ""))

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


def build_config(tmpdir, body=""):
    p = tmpdir.mkdir("penpath")
    pen_path = p.strpath

    base_config_header = """{
    "pen" : {
        "penPath" : "%s",
        "downloadFolder" : "%s",
        "common" : {
            "writesubtitles" : true,
            "format" : "quality_setting_from_common"
            }
    },
    "source" : [
    """ % (pen_path, base_download_folder)

    base_config_footer = """    ]
}"""

    config = base_config_header + body + base_config_footer

    return config, pen_path


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
                "url" : "https://url4.com",
                "description" : "Url 4",
                "prefix" : "PREFIX_"
            },
            {
                "" : true,
                "url" : "https://malformedsource.com",
                "description" : "Malformed, log but don't quit"
            },
            {
                "deactivated" : true,
                "url" : "https://urlx.com",
                "description" : "Url x"
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
            "https://url4.com",
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

    assert processed_params[3]["outtmpl"].startswith(pen_path + "/" + base_download_folder + "/" + "PREFIX_")

    # Check if output path contains the base path and download folder name from the config
    assert processed_params[0]["outtmpl"].startswith(pen_path + "/" + base_download_folder)
    assert processed_params[1]["outtmpl"].startswith(pen_path + "/" + base_download_folder)


def test_run_file_copy_one_file_does_not_exist_one_file_does(tmpdir):
    """ Check if a file has been copied and if a file is already existing, not being copied """

    temp = tmpdir.mkdir("source")
    p = temp.join("testfile.mp4")
    
    random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(200)])

    p.write(random_string)

    src_file_path = p.strpath

    p = temp.join("already_there.mp4")
    p.write(random_string)

    src_file2_path = p.strpath

    config, pen_path = build_config(tmpdir, """
            {
                "path" : "%s",
                "description" : "File which is not already there"
            },
            {
                "path" : "%s",
                "description" : "File which is already there"
            }
    """ % (src_file_path, src_file2_path))

    # Write file with appendix to detect later if it was changed or not.
    # Commute tube does only check the first 100 bytes for performance
    # reasons. This logic exploits this logic. 

    os.mkdir(pen_path + "/" + base_download_folder)
    with open(pen_path + "/" + base_download_folder + "already_there.mp4", "w") as text_file:
        text_file.write(random_string + "_FILE_WAS_HERE_BEFORE_APPENDIX")

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[],
        to_be_downloaded_urls=[
        ]
    )

    assert processed_params == []

    assert "testfile.mp4" in os.listdir(pen_path + "/" + base_download_folder)
    assert "already_there.mp4" in os.listdir(pen_path + "/" + base_download_folder)

    with open(pen_path + "/" + base_download_folder + "already_there.mp4", 'r') as tmpfile:
        possible_unaltered_file = tmpfile.read().replace('\n', '')

    assert possible_unaltered_file == random_string + "_FILE_WAS_HERE_BEFORE_APPENDIX"


def test_run_file_copy_but_exists_in_place_and_is_different(tmpdir):
    """ Test if a file exists and is different, file should be overwritten """

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
    target_file_name = target_folder + "/testfile.mp4"
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


def test_check(tmpdir):
    """ Test for check logic argument """

    config, pen_path = build_config(tmpdir)

    print(config)

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
            "--check"
        ],
        to_be_downloaded_urls=[
        ]
    )


def test_set_no_format_at_all(tmpdir):
    """ Test if standard commute-format is set if no format is set at all"""

    config = """{
    "pen" : {
        "penPath" : "%s",
        "downloadFolder" : "Download",
        "common" : {
            }
    },
    "source" : [
            {
                "url" : "https://url1.com",
                "description" : "Url 1",
                "playlistend" : 3
            }
        ]
    }""" % (tmpdir.mkdir("penpath").strpath)

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
        ],
        to_be_downloaded_urls=[
            "https://url1.com"
        ]
    )

    assert processed_params[0]["format"] == "bestvideo+bestaudio/best"


def test_set_format_by_command_flag_in_debug_mode(tmpdir):
    """ Test if common format is overwritten by command flag in debug mode """

    config = """{
    "pen" : {
        "penPath" : "%s",
        "downloadFolder" : "Download",
        "common" : {
                "format" : "common_format"
            }
    },
    "source" : [
            {
                "url" : "https://url1.com",
                "description" : "Url 1",
                "playlistend" : 3
            }
        ]
    }""" % (tmpdir.mkdir("penpath").strpath)

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
            "--debug",
            "--format",
            "command-line-format"
        ],
        to_be_downloaded_urls=[
            "https://url1.com"
        ]
    )

    assert processed_params[0]["format"] == "command-line-format"
    assert processed_params[0].get("simulate")


def test_filter_source(tmpdir):

    config = """{
    "pen" : {
        "penPath" : "%s",
        "downloadFolder" : "Download",
        "common" : {
                "format" : "common_format"
            }
    },
    "source" : [
            {
                "url" : "https://url1.com",
                "description" : "Url 1",
                "playlistend" : 3
            },
            {
                "url" : "https://url2.com",
                "description" : "Url 2",
                "playlistend" : 3
            }
        ]
    }""" % (tmpdir.mkdir("penpath").strpath)

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
            "--filter",
            "Url 2"
        ],
        to_be_downloaded_urls=[
            "https://url2.com"
        ]
    )

def test_check_pen_can_be_mounted_not_mounted(tmpdir):

    def mock_ismount(input):
        return False

    monkeypatch.setattr(os.path, 'ismount', mock_ismount)

    config, pen_path = build_config(tmpdir, "")

    init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
            "--check"
        ],
        to_be_downloaded_urls=[]
        )

def test_check_pen_can_be_mounted_already_mounted(tmpdir):

    def mock_ismount(input):
        return True

    monkeypatch.setattr(os.path, 'ismount', mock_ismount)

    config, pen_path = build_config(tmpdir, "")

    init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[
            "--check"
        ],
        to_be_downloaded_urls=[]
        )