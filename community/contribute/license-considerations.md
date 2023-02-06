# License considerations for SCS

As Sovereign Cloud Stack ([SCS](https://scs.community/)), our mission is to provide Operators
(be it Cloud Service Providers or just internal IT departments) with a well working software
stack, that avoids exposing them to legal risks or additional restrictions that limits the
usefulness. Free software licenses have this intention but differ in how they achieve it and in
what kind of protections they provide. In the first approximation, all [OSI](https://opensource.org/licenses)-approved
open source licenses can be considered as valid options. As a matter of fact,
we do consider projects under such licenses as valid modules for SCS -- where we
use such projects and adjust or extend them, we would provide our contributions
under the license terms of the respective project, so we can achieve our goal to feed back code
upstream to the respective project, contribute to it and avoid fragmentation.

Where we do create independent code, we do have additional preferences, though.

For our own code, we do prefer the [Affero General Public License version 3](https://www.gnu.org/licenses/agpl-3.0.html)
(AGPLv3) as license. Likewise, for documentation, we prefer [CC-BY-SA](https://en.wikipedia.org/wiki/CC-BY-SA).
Where we create standard libraries to interface with our software, we would
consider the [LGPLv3](https://www.gnu.de/documents/lgpl-3.0.en.html) for these,
as we don't want interaction with our platform to be seen as requiring licensing
code.

## Reciprocity

The GPL family of licenses are reciprocal licenses -- sometimes called [copyleft](https://en.wikipedia.org/wiki/Copyleft)
licenses -- the recipient of the licensed code can make all sorts of modifications,
but if she uses the code to release software (GPL) or provide a networked service
(AGPL) to others, then she must grant the same rights to the recipients -- this
includes making the modifications available under the same terms as the received software.
Microsoft has infamously [attacked](https://web.archive.org/web/20010615205548/http://suntimes.com/output/tech/cst-fin-micro01.html)
copyleft licenses (and specifically the GPL) as cancerous "viral" license.

Reciprocity has many advantages:

* Code that has been created as free software will stay free. While GPL code can be
  combined in a larger software collection with proprietary software, the code itself
  including its enhancements etc. (technically: all derived works, see below) will
  remain free.

* The obligation to make the changes available avoids fragmentation. As changed and
  "improved" versions need to be made available, it is much easier to review and feed
  those changes back and create a unified upstream codebase that reflects the needs of
  the complete user base by including the needed changes. This was observed and
  [reported](https://lwn.net/Articles/660428/) by Martin Fink (HP's former CTO).

The hugely successful [Linux kernel](https://kernel.org/) project uses the GNU GPL;
many of the more traditional key projects in the open source world use copyleft licenses such as
the AGPL, GNU GPL, GNU LGPL, MPL or the [OSL](https://opensource.org/licenses/OSL-3.0).

## Controversy

* Not fulfilling the license terms of a software license typically leads to the ability for the
  license owner to revoke the license -- as it is relatively easy to not fulfill all obligations
  of the GPL out of sheer negligence, the revocation without prior warning seems
  disproportionate -- this is sometimes called the GPL death penalty.  The open source community
  though has a strong interest in bringing every licensee into compliance by giving violators a
  fair chance to correct their behavior. SCS explicitly supports the [GPL Cooperation Commitment](https://gplcc.github.io/gplcc/)
  and the respective [document](https://www.kernel.org/doc/html/v4.15/process/kernel-enforcement-statement.html)
  from the Linux kernel developers and pledges to give violators a warning and a chance to correct action
  by allowing for a cure period. This is a bit of a legacy issue -- it is relevant to (L)GPLv2
  code only -- v3 of L/A/GPL does already contain language that has cure provisions, so it's
  clear by the licensing terms.

* Many companies seem to be worried that they will inadvertently violate the GPL by negligence.
  And it is true that a company needs a tighter control of the usage of inbound source code
  which comes with a reciprocal license than the permissive BSD 3-clause or Apache Software (v2)
  licenses. This advantage however quickly turns into a disadvantage as soon as the company does
  significant outbound open source contributions under a permissive license -- they rarely want
  to give their competitors an opportunity to consume their contributions and then add
  proprietary changes to gain an advantage.  In general, companies are well advised to have a
  detailed understanding of all code that is being used and contributed and their respective
  license terms -- for proprietary and open source code and for reciprocal and for permissive
  licenses.  Some companies have successfully installed license review boards or
  [open source review boards](https://www.linuxfoundation.org/resources/open-source-guides/using-open-source-code/)
  to create oversight, recommendations and policies to ease the governance.

Despite this, many of the recent open source projects, especially in the cloud world
have adopted permissive licenses, such as X11, BSD 3-clause, MIT and especially the popular
[Apache software license](https://en.wikipedia.org/wiki/Apache_License>) (ASL2), as it
appears to allow for faster adoption by companies that may not have mature open source
policies in place or that simply have overly careful lawyers which may be influenced
by the scare tactics some bad companies have built on top of copyleft licenses.

## Affero

The reciprocity of the GNU GPL does not apply on the *creation* of a derived work. A company
can consume GPL'ed code and change it to their own liking without ever making any the
changes available if only used in-house. The terms however do apply as soon as the derived
work is *released*, i.e. the software is passed on to a third party.

In modern times, software is often used to provide a *networked service* (think SaaS) to third
parties. Unlike the standard GPL, the Affero GPL (AGPL) does consider the act of making it
available in such a way as similar to releasing the software and does require that applied
changes to the software are being made available in this case.

The AGPL thus closes a shortcoming in the traditional non-Affero GPL for a world that
increasingly moves towards networked services.

The very successful [Nextcloud](https://nextcloud.org/) project uses the AGPLv3.

## Derived works and Strong vs. Weak Copyleft

What exactly constitutes derived work needs to be defined -- it's one of the questions where
copyright law can get subtle. From a practical view, consuming (non-trivial) source code and
binary linking is typically considered creating derived works. Whereas interacting via a network
API or starting another process is typically considered a copyright boundary.  To avoid any
unclarity, the Linux kernel community has explicitly called out using Linux system calls (which
includes using the interface definitions) is a copyright boundary and can thus be done by
applications without any license implications.

Considering linked code to be derived works (as is the case in the GPL and AGPL) and thus
requiring it under the same (or a compatible) copyleft license is considered a Strong Copyleft
license.

Libraries are often providing implementations for standard services and helpers; it may not be
reasonable to consider applications that want to use a library as derived works from that
library and requiring the application to thus be licensed under a (compatible) copyleft license.
For these libraries, a Weak Copyleft license (such as the [LGPL](https://www.gnu.org/licenses/lgpl-3.0.en.html)
or the [EPL](https://www.eclipse.org/legal/epl-2.0/) can be used.  This would still require changes to
the library *itself* to me made available under the copyleft license but would make binary
linking (including the use of interface definitions) a copyright barrier and thus allow for
non-copylefted code to be linked against a weakly copylefted library. This license is used by
many of the standard and system libraries in the Linux world and is often a good choice for
libraries of standardized services.

## Patents

Free software licenses are intended to give users broad rights -- the GNU GPL talks about the
[four freedoms](https://fsfe.org/freesoftware/) to use software for any purpose, to study and
adjust the software (this needs source code access), to redistribute the software and to improve
it and to make these improvements available.

Software patents can significantly subvert the intended rights -- the open source community in
general dislikes software patents for this and many other reasons that are discussed
[elsewhere](https://en.wikipedia.org/wiki/Software_patents_and_free_software) .
In some countries, there are rules that prevent pure software from being patented, though [not
all patent offices are fully following these rules](https://en.wikipedia.org/wiki/Software_patents_under_the_European_Patent_Convention).

As software patents are existing and a serious danger to the open source goals, there are a few
attempts to improve the situation. The Apache Software License (a permissive license), requires
code contributors to grant a patent license to all downstream recipients of the code
to use the contributed code by itself or in combination with the project that it was contributed
to and makes a possible patent holder lose its license rights should he nevertheless try to
assert a patent against the thus licensed use. The (A)GPLv3 has a similar clause.

The [Open Invention Network](https://www.openinventionnetwork.com/) (OIN) has a meanwhile
huge patent pool that is cross-licensed between all participants and which can freely be used
in a large list of covered open source software by everyone, except for those that raise patent
violation claims against any of the covered open source projects. This basically restricts
those patents to be only used defensively in the context of the covered open source projects.

Should SCS be in a position to make inventions that should be protected by a software patent,
it pledges to contribute these to the OIN pool.

## Copyright Assignments and Contributor License Agreements

Very few Open Source projects require copyright assignment; the GNU projects are the
only commonly used ones that the author is aware of. This results in fully centralized
copyright ownership. This puts the FSF into a very
strong position -- a position to enforce copyright, to change licenses etc. This requires
a lot of trust towards the copyright assigneed.

Most open source projects prefer distributed copyright -- the authors (or their
employers) retain the copyright to their works. They grant a license for the open
source project to use and integrate and redistribute the work -- typically the
license grant is extended to the public. In a sufficiently distributed copyright model,
it is very hard to change a license, as all copyright holders would need to agree.
This can both be considered advantageous and disadvantageous.

Many software projects use [Contributor License Agreements](https://en.wikipedia.org/wiki/Contributor_License_Agreement)
(CLAs), documenting that contributed code grants certain rights to the project
owner (a foundation or sometimes a company). This ensures that the project owner
has all needed rights to use, protect, redistribute ... the code. If the CLA contains
*copyright assignment*, it also allows the project to change the license or to
create derived works under a different license.

While this is advantageous for the project owner, it is not necessarily advantageous for the
code contributor.

Copyright enforcement does not require all copyrights to be held by a legal entity. Any holder
of significant copyrights can actually enforce it against violators.

The Linux kernel and an increasing number of projects do not work with copyright assignments
nor CLAs, but with [Developer Certificates of Origin](https://en.wikipedia.org/wiki/Developer_Certificate_of_Origin)
(DCO -- the signed-off lines of kernel commits).  This is deemed sufficient to document the origin and the authorization to
contribute code.

The SCS project will not change the license. There however might be cases, where potential users
can not consume AGPL'ed or LGPL'ed code (due to corporate policies, e.g. based on bad experience,
immature license governance practices or lawyers that panic). Our goal would be to ensure that our
licensing terms and all other pledges provide the assurance needed that users do not need to be
afraid of the AGPL. The cure provisions from v3 of the GPL license family actually also help to
avoid unnecessary fear. However, unfortunately, some "open source" companies in the past have
abused copyleft with a scare and sell a proprietary license tactics to make money, which has
hurt copyleft acceptance significantly. We might thus not be successful and need to somehow
accept not serving all users or come up with a relicensing scheme that can not corrupt
ourselves. We are following the copyleft-next discussion to work out how we can best achieve
this, but have not yet found the silver bullet. This might have an influence how we do DCOs,
maybe under a permissive license, or maybe need to use CLAs.

## License in = License out

It is best practice that open source projects grant their downstream users the same
license rights as they received contributions under. Or worded the opposite direction:
It is best practice to require no more rights to be granted from upstream contributors
(in the CLA or DCO) than the projects grants to downstream consumers of the project.
SCS follows this best practice.

## Further reading

* <https://en.wikipedia.org/wiki/Comparison_of_free_and_open-source_software_licences>
* <https://en.wikipedia.org/wiki/Software_patents_and_free_software>
* <https://joinup.ec.europa.eu/collection/eupl/matrix-eupl-compatible-open-source-licences>
* <https://lwn.net/Articles/592503/>
* <https://sfconservancy.org/blog/2020/jan/06/copyleft-equality/>
* <https://developercertificate.org>
* <https://julien.ponge.org/blog/developer-certificate-of-origin-versus-contributor-license-agreements/>
