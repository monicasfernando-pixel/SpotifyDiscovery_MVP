Static Myntra-style mobile prototype.

```
index.html
css/styles.css
js/
  app.js                 # chrome, navigation, events
  state.js
  data/                  # sample catalog + verdict labels
  rules/                 # verdict engine, grouping, bag-nudge pick
  ui/                    # formatters + product art
  components/            # product card, verdict strip, triage, bag strip
  screens/               # wishlist, bag, home/category/studio stubs
```

Preview locally with `npx --yes serve .` then open http://localhost:3000 (or the port shown). Deploy with `npx --yes vercel login` then `npx --yes vercel --yes --prod`.
