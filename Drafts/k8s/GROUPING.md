# Grouping of repositories on the CI dashboard

Grouping of repositories on the CI dashboard should be implemented using Github repository "topics". The update script will read topics from the Github API and will group the repositories accordingly.

In order to keep the code of the update script generic and to make adding more topics/sections as simple as possible, a prefix for grouping should be used.

The actual wording of the prefix is not important for the grouping. For the sake of illustration, consider the following example:

`priority-` resulting in e. g. `priority-r0`/`priority-r1`/`priority-backlog`.

The update script should be able to recognize this information and represent it accordingly in the dashboard output.
