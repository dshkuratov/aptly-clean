#!/usr/bin/env python
from __future__ import print_function
import argparse
import sys
import apt_pkg
import subprocess


def parse_arguments(args=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        help="Run in dry mode, without actually"
             "deleting the packages."
             "them.",
        action="store_true"
    )
    parser.add_argument(
        "--repo",
        dest="repo",
        help="Which repository should be searched?",
        type=str,
        required=True
    )
    parser.add_argument(
        "--package-query",
        dest="package_query",
        help="Which packages should be removed?\n"
             "e.g.\n"
             "  - Single package: ros-indigo-rbdl.\n"
             "  - Query: 'Name (%% ros-indigo-*)' "
             "to match all ros-indigo packages. See \n"
             "https://www.aptly.info/doc/feature/query/",
        type=str,
        required=True
    )
    parser.add_argument(
        "-n",
        "--retain-how-many",
        dest="retain_how_many",
        help="How many package versions should be kept?",
        type=int,
        required=True
    )
    return parser.parse_args(args)


def query_packages(repo, package_query):
    output = subprocess.check_output([
        "aptly",
        "repo",
        "search",
        "-format='{{.Package}}'",
        repo,
        package_query
    ])
    return unique_output(output)


def get_sorted_versions_list(repo, package):
    apt_pkg.init_system()
    output = subprocess.check_output([
        "aptly",
        "repo",
        "search",
        "-format='{{.Version}}'",
        repo,
        package
    ])
    return sorted(
        unique_output(output),
        cmp=apt_pkg.version_compare,
        reverse=True
    )


def unique_output(output):
    splited_output = output.split("\n")
    striped_output = map(str.strip, splited_output)
    filtered_output = filter(None, striped_output)
    unique_output = set(filtered_output)
    return unique_output


def purge_package(repo, package, retain_how_many, dry_run):
    version_list = get_sorted_versions_list(repo=repo, package=package)
    if len(version_list) <= retain_how_many:
        print('Package {} not have versions for deleting'.format(package))
        return "nothing to do"

    keep_versions_newer = version_list[retain_how_many]
    print(
        'Remove packages whose versions are older than {}'.format(
            keep_versions_newer
        )
    )
    output = subprocess.check_output([
        "aptly",
        "repo",
        "remove",
        "-dry-run=" + str(dry_run),
        repo,
        "'Name ({}), $Version  (<= {})'".format(
            package, keep_versions_newer
        )
    ])
    print(output)
    return "done"


def purge(repo, package_query, retain_how_many, dry_run):
    packages = query_packages(repo=repo, package_query=package_query)
    if not packages:
        sys.exit("No packages to remove.")
    for package in packages:
        purge_package(
            repo=repo,
            package=package,
            retain_how_many=retain_how_many,
            dry_run=dry_run
        )


def main():
    args = parse_arguments()
    if args.dry_run:
        print("Run in dry mode, without actually deleting the packages.")

    print(
        'Remove package query({}) from {} repo'
        ' and keep the last {} versions'.format(
            args.package_query, args.repo, args.retain_how_many
        )
    )
    purge(
        repo=args.repo,
        package_query=args.package_query,
        retain_how_many=args.retain_how_many,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
