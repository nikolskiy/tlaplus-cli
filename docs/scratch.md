# Scratchpad

## fixes

- When nothing is pinned and a version is installed, it should be used as the pinned version. Make sure that if the version is pinned and another version is installed the pinned version doesn't change. Write a test for those cases.
- Upgrade and version list is not working correctly. The list shows that the verision can be upgraded even if it is up to date. 
- There are problems with displaying installed tag and available. The list command shows only what is available but not the tag that is installed.
- Show date published as well if possible
- If upgrade is called on the pinned version the pin should point to the new tag.
- Uninstall removes all available tags. It should ask which version to uninstall if there are multiple versions installed. It should take `--all` flag to remove all versions. Write a test for that.
- Find only shows the path to the jar. It should show:
    ```text
    TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
    /home/bob/.cache/tla/tlc/v1.8.0-5a47802/tla2tools.jar
    ```
- To `tla tlc list` add date when version was released.
- upgrade doesn't remove the old version. Maybe it should.
- the list shows "yes" instead of green checkmark.
- Rename "find" to "path".
- The name find is confusing because it feels like you can search for any version or tag. But that functionality is not there and hard to implement.
- If some version is installed we should always have some pinned version. There should not be a state where no version is pinned. If a version is uninstalled the pin should point to the latest installed version. If no version is installed the pin should be removed.
- "tla tlc dir" should show the directory and it's content (list of installed versions).