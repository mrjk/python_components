# Fork

This is a fork for the following reasons:

* I had a bug on var parsing on some edge cases
    * I tried to analyse the code and fix it
    * Eventually I fixed it, but then I hit other annoying bugs
        * This time I could not make it, because I'm too unfamiliar in how the original 
        author wrote the code. However I liked how this library was designed, and I really appreaciate
        what the original author did, but it was not fitting well to my original purpose of fixing
        bugs and eventaully add few new features ors options.
* Let's transform the whole code into a class based code. It makes things way much easier
    to read and maintain. Also fixing bugs became way much easier, and option management has been simplified.
    Thus, I add few more options, and fixed some errors edge cases. The idea is too stay around original
    shell behavior (ideally POSIX or later), but it need to be more tested to validate.
    * Use git diff to see patches and differences


## Last 
```
* 1b8b543 (HEAD -> develop, origin/develop, origin/dev-pid-feature-switch, dev-pid-feature-switch) Fix issues on cases with $$ or more (mrjk, Thu Feb 6 04:36)
* 47c7570 Fix issue on resolving empty var names (mrjk, Thu Feb 6 04:35)
* d5b9047 Fix non string concatenation error on non string values (mrjk, Thu Feb 6 04:29)
| *   fbd87f5 (refs/stash) WIP on dev-classes: 0aaeb0c change: make some methods internal to visibility (mrjk, Thu Feb 6 02:52)
| |\
| | * b4f0e2f index on dev-classes: 0aaeb0c change: make some methods internal to visibility (mrjk, Thu Feb 6 02:52)
| |/
* | 2ac0146 Add support for kwargs (mrjk, Thu Feb 6 02:44)
* | a7f4911 Add code comments (mrjk, Thu Feb 6 02:44)
* | 665a3cf Add option to disable pid processing (mrjk, Thu Feb 6 02:42)
|/
* 0aaeb0c (origin/dev-classes, dev-classes) change: make some methods internal to visibility (mrjk, Thu Feb 6 02:02)
* 1c50578 Lint code with pylint and black (mrjk, Thu Feb 6 01:58)
* b82abad refactor: functions to ExpandParser class (mrjk, Thu Feb 6 01:48)
* e8c7cf9 (origin/master, origin/HEAD, master) Final cleanup (Arijit Basu, Nov 22 2023)
```
