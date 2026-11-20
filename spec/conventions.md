# Conventions

This file gives the conformance clause, the observation vocabulary and the
notation of the Slate specification. Text in a `text` block is normative. Text
outside a block is a note.

## Conformance

```text
Levels: must (its absence can block or mislead a user), should.
Outcomes of a check on a build: passed, failed, inapplicable.
A rule is inapplicable on a stack only if the modality sheet of that stack lists an adaptation
  that keeps the intent of the rule.
The inventory is closed. A place, state or content item that no face lists does not exist.
A trigger that no rule names keeps the platform default.
Frame rule: a rule changes only what it names.
Quoted text is exact. In a quoted example, a card identifier, a column name, a label, the name
  of a person, a number and a count word stand for the values of the case at hand:
  "Moved SL-103 to Ready." is "Moved SL-107 to Review." for that card and that column.
Every rule has the origin "extracted" (from the reference build).
A "Fail:" line names a behavior that is wrong. A build that shows it fails the rule. No build
  has confirmed these lines yet.
```

## Observation vocabulary

A rule states its effect only with these words. A check observes only these.

```text
place          the top-level view that is shown
text           a string that the user can perceive
role           a role concept (below)
name           the name of a part, as a user perceives it
state          a perceivable state of a part: on, off, mixed, chosen, selected, disabled, a mark
focus          the part that takes key input, or "none"
announcement   a text that is given to a user who cannot see the screen
address        the address of the current history entry, as a place and its parts (DAT-16)
history depth  the number of history entries
scroll         top, restored, or "in view" for a part
request        a call to the service (fixture/fixture.md), by operation
```

## Role concepts

```text
place title    the one title of a place; it can take focus
up-link        a link to the parent place
link           a link to a place
action         a control that does one thing when the user activates it
toggle         a control that is on or off (bulk toggles can be mixed)
choice         one option of a set in which exactly one is chosen
field          a control that takes text
card           one card in a column; its name is its identifier and its title
column         one column of the board; its name is the column name
notice         the one notice of the app
alert          a text that reports a failure in place; it is announced at once each time it shows
status line    a text that reports a count
heading        a title of a part of a place
mark           a short text that shows a temporary state of a part: "Saving…", "Sending…", "Moving"
placeholder    a block that stands for content that is loading; it has no text
```

## Notation

```text
States line:   <Region>  States: A | B (B1 | B2) | C
State name:    <Region>.<State>, for example Column.Loading.Slow
Face:          "<Region>.<State> face", then one line for each content item in reading order:
               number, rank rN (a build without room drops the highest number first),
               emphasis P | N | Q (primary, normal, quiet), item. Sub-items use letters.
Item name:     <Region>.<State>.<number><letter>, for example Board.Ready.2d
Rule:          a header line, then one EARS sentence.
               Header: identifier, [level], [capability] if one applies, "origin:", "sets:" with
               the regions that the rule can change, "overrides" with an identifier if one applies.
EARS forms:    While <state>, when <trigger>, Slate shall <effect>.
               When <trigger>, Slate shall <effect>.
               If <fault>, then Slate shall <effect>.
               While <state>, Slate shall <effect>.     Slate shall <effect>.
Trigger:       an intent or an event from the closed lists in app.md, in the same words.
Table:         a header line with identifier, [level], "decides:" with a trigger, "owns:" with
               regions, then rows. The first row that matches wins. The last row is "otherwise".
Row name:      <Table>.<number>, for example NAV-T1.2
Capability:    [pointer] needs a pointing device. [keys] needs a keyboard. [graphic] needs a
               graphic display.
```

## Terms

```text
visible card     a card that the filter does not hide, in a column in state Column.Cards
hidden card      a card that the filter hides
board order      the columns in their order, then the cards from the top of each column
position         the place of a card in its column, counted from 1 at the top
focus stop       the one card that takes focus when focus comes to the cards (FCS-1)
apply the filter the effect of FLT-8
raise a notice   show a notice in region Notice (NTC-1)
session          the time from a start or a reload to the next reload
```
