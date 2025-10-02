# Virtual RC Pets

This bot provides the Pets in the [RC](https://www.recurse.com/) instance of RC
Together.

Lots of Recursers have contributed this project, and I'd love to have more
fun things. I will merge any PRs from Recursers.

## Instructions

Available pets can be seen in the Agency just above the main space. To adopt a
pet send a message to the genie:

```
@**Pet Agency Genie** May I please adopt the dragon?
```

Remember to be polite! Only a limited selection of pets are available in the
agency at any time. If the Agency is short of pets you can restock with:

```
@**Pet Agency Genie** It's time to restock!
```

The oldest pet in the agency will be removed, and then all free spaces will be filled.

If you're tired of your pets, you can get rid of them with:

```
@**Pet Agency Genie** Abandon my parrot!
```

You can also ask the agency to look after your pets:

```
@**Pet Agency Genie** Look after my pets!
```

Or you can put just a single pet into day care. The main purpose for this is to stop them
getting in the way when you're trying to edit the space. Don't forget to collect them again!

```
@**Pet Agency Genie** It's time to collect my pets.
```

You can also give pets to people, and pet other people's pets!

## Design

+ A sloppy natural language interface made with regexes: [pets/parser.py]
+ Gamification with artificial scarcity.
+ Stateless controller! All long term storage is in the RC Together server.
