# Developer Certificate of Origin + Licenses

The Developer Certificate of Origin (DCO) is a lightweight way for contributors
to certify that they wrote or otherwise have the right to submit the code they
are contributing to the Sovereign Cloud Stack.

```bash
By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

All contributions to the Sovereign Cloud Stack are licensed under the
(OSI approved) open source license of the upstream project being used therein
(very often this is the [Apache Software License v2](https://www.apache.org/licenses/LICENSE-2.0)).

Where we create independent code, we prefer to use the [GNU Affero General Public License 3](https://www.gnu.org/licenses/agpl-3.0.html),
except for interface code which we would put under LGPL-3 (weak copyleft).
Own documentation content is licensed under [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Contributors sign-off that they adhere to these requirements by adding a `Signed-off-by`
line to commit messages.

```bash
My fancy commit message

Signed-off-by: Christian Berendt <berendt@betacloud-solutions.de>
```

Git has a `-s` command line option to append this automatically to your commit message:

```bash
git commit -s -m 'My fancy commit message'
```

The status of a pull request is set to failed if commits do not contain a valid `Signed-off-by` line.

![Failed DCO in GitHub](github-failed-dco.png)

Considerations behind the choice of AGPLv3, CC-BY-SA and the usage of the DCO can be found [here](license-considerations.md).

## Further reading

- <https://developercertificate.org/>
- <https://julien.ponge.org/blog/developer-certificate-of-origin-versus-contributor-license-agreements/>
- <https://lwn.net/Articles/592503/>
