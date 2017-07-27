import pytest
import mock
import aptly_clean


@pytest.mark.parametrize("input, match", [
    [
     [
      "--dry-run", "--repo", "xenial", "--package-query", "dibctl",
      "-n", "1"
     ],
     {
      "dry_run": True, "repo": "xenial",
      "package_query": "dibctl", "retain_how_many": 1
     }
    ],
    [
     [
      "--repo", "debian", "--package-query", "'Name (dibctl)'",
      "--retain-how-many", "40"
     ],
     {
      "dry_run": False, "repo": "debian",
      "package_query": "'Name (dibctl)'", "retain_how_many": 40
     }
    ],
    [
     [
      "--dry-run", "--repo", "stable", "--package-query", "'Name (dibctl)'",
      "-n", "10"
     ],
     {
      "dry_run": True, "repo": "stable",
      "package_query": "'Name (dibctl)'", "retain_how_many": 10
     }
    ]
])
def test_parse_arguments(input, match):
    args = aptly_clean.parse_arguments(input)
    assert args.dry_run == match["dry_run"]
    assert args.repo == match["repo"]
    assert args.package_query == match["package_query"]
    assert args.retain_how_many == match["retain_how_many"]


def test_query_packages():
    with mock.patch.object(
        aptly_clean.subprocess,
        "check_output",
        return_value="packpack\n" * 100
    ) as mock_run:
        result = aptly_clean.query_packages("xenial", "packpack")
        assert result == set(["packpack"])
        assert (
            ' '.join(mock_run.call_args[0][0]) ==
            "aptly repo search -format='{{.Package}}' xenial packpack"
        )


@pytest.mark.parametrize("output, match", [
    [
     """0.2.1+0~20161215150040.32~1.gbp772662
0.3.4+0~20161230151752.48~1.gbp53b93d
0.5.1+0~20170405090958.58~1.gbp184c94
0.3.3~20161227210747.44
      """, [
            "0.5.1+0~20170405090958.58~1.gbp184c94",
            "0.3.4+0~20161230151752.48~1.gbp53b93d",
            "0.3.3~20161227210747.44",
            "0.2.1+0~20161215150040.32~1.gbp772662"
            ]
    ],
    [
     """0.2.1+0~20161215150040.32~1.gbp772662
0.3.4+0~20161230151752.48~1.gbp53b93d
0.5.1+0~20170405090958.58~1.gbp184c94
0.3.3~20161227210747.44
      """, [
            "0.5.1+0~20170405090958.58~1.gbp184c94",
            "0.3.4+0~20161230151752.48~1.gbp53b93d",
            "0.3.3~20161227210747.44",
            "0.2.1+0~20161215150040.32~1.gbp772662"
            ]
    ],
    [
     """0.2.1+0~20161215150040.32~1.gbp772662
0.3.4+0~20161230151752.48~1.gbp53b93d
0.5.1+0~20170405090958.58~1.gbp184c94
0.3.3~20161227210747.44
      """, [
            "0.5.1+0~20170405090958.58~1.gbp184c94",
            "0.3.4+0~20161230151752.48~1.gbp53b93d",
            "0.3.3~20161227210747.44",
            "0.2.1+0~20161215150040.32~1.gbp772662"
            ]
    ],
])
def test_sorted_versions_list(output, match):
    with mock.patch.object(
        aptly_clean.subprocess,
        "check_output",
        return_value=output
    ) as mock_run:
        result = aptly_clean.get_sorted_versions_list("xenial", "dibctl")
        assert result == match
        assert (
            ' '.join(mock_run.call_args[0][0]) ==
            "aptly repo search -format='{{.Version}}' xenial dibctl"
        )


@pytest.mark.parametrize("input, match", [
    ["", set()],
    ["foo\nfoo", set(["foo"])],
    ["foo\nbar", set(["foo", "bar"])],
    ["foo\n", set(["foo"])],
    ["foo", set(["foo"])],
    ["\n\n\nfoo\nfoo\nfoo\n\nbar\n\n", set(["foo", "bar"])],
    ["\n   \n \nfoo\nfoo\nfoo\n\nbar\n\n", set(["foo", "bar"])],
    ["text with spaces", set(["text with spaces"])]
])
def test_unique_output(input, match):
    assert aptly_clean.unique_output(input) == match


@pytest.mark.parametrize("sorted_versions_list, retain_how_many, match", [
    [
        [
         "0.5.1+0~20170405090958.58~1.gbp184c94",
         "0.3.4+0~20161230151752.48~1.gbp53b93d",
         "0.3.3~20161227210747.44",
         "0.2.1+0~20161215150040.32~1.gbp772662"
        ],
        2,
        "0.3.3~20161227210747.44"
    ],
    [
        [
         "0.5.1+0~20170405090958.58~1.gbp184c94",
         "0.3.4+0~20161230151752.48~1.gbp53b93d",
         "0.3.3~20161227210747.44",
         "0.2.1+0~20161215150040.32~1.gbp772662"
        ],
        4,
        ""
    ],
    [
        [
         ""
        ],
        4,
        ""
    ]
])
def test_purge_package(sorted_versions_list, retain_how_many, match):
    with mock.patch.object(
        aptly_clean,
        "get_sorted_versions_list",
        return_value=sorted_versions_list
    ):
        with mock.patch.object(
            aptly_clean.subprocess,
            "check_output",
            return_value=""
        ) as mock_run:
            result = aptly_clean.purge_package(
                "xenial",
                "dibctl",
                retain_how_many,
                False
            )
            if len(sorted_versions_list) <= retain_how_many:
                assert(result == "nothing to do")
            else:
                assert(result == "done")
                assert (
                    ' '.join(mock_run.call_args[0][0]) ==
                    "aptly repo remove -dry-run=False xenial 'Name (dibctl)," +
                    " $Version  (<= {})'".format(match)
                )
