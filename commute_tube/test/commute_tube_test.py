import sys
import pytest
from commute_tube.__main__ import main, CommuteTube
from _pytest.monkeypatch import MonkeyPatch
import json
import youtube_dl

# Strategy
# 1. Write config to temp file
# 2. Start main with temp file as argument
# 3. Check if mock has been called
# 4. Check if files are in stdout

base_config_header = """{
    "pen" : {
        "penPath" : "/tmp/commuteUSB",
        "mountAndUnmount" : "False",
        "downloadFolder" : "Download",
        "common" : {
            "writesubtitles" : true,
            "format" : "quality_setting_from_common"
            }
    },
    "source" : [
    """

base_config_footer = """    ]
}"""

def init_commute_tube(tmpdir, config, additional_args, to_be_downloaded_urls):

    monkeypatch = MonkeyPatch()
    downloaded_urls = []

    params = []

    def mockdownload(ytdl, source):
        logger = ytdl.params['logger']
        logger.debug("Passed parameters: " % ytdl.params)
        downloaded_urls.append(source[0])
        params.append(ytdl.params)

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
    assert pytest_wrapped_e.value.code == 0

    assert downloaded_urls == to_be_downloaded_urls

    return params

def build_config(body):
    return base_config_header + body + base_config_footer


def test_run1(tmpdir):

    config = build_config("""
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
                "shellscript" : "printf 'https://url3fromshell.com\\nhttps://url4fromshell.com'",
                "description" : "Shellscript",
                "playlistend" : 3
            }
    """)

    processed_params = init_commute_tube(
        tmpdir=tmpdir,
        config=config,
        additional_args=[],
        to_be_downloaded_urls=["https://url1.com", "https://url2.com", "https://url3fromshell.com", "https://url4fromshell.com"]
    )

    assert processed_params[0]["format"] == "quality_setting_from_common" 
    assert processed_params[1]["format"] == "quality_setting_from_source" 
