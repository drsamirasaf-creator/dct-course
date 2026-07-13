# Deploying dct-course to GitHub Pages

All commands run in Terminal from inside the `dct-course` folder.

## 1. One-time: create the repo and push
git init
git add .
git commit -m "DCT course website"
Then either: gh repo create dct-course --public --source=. --push
Or (browser): create empty public repo `dct-course` on github.com, then:
git remote add origin https://github.com/<YOUR-USER>/dct-course.git
git branch -M main
git push -u origin main

## 2. Publish
quarto publish gh-pages
Site appears at https://<YOUR-USER>.github.io/dct-course/ within ~2 minutes.

## 3. Every update afterwards
git add . && git commit -m "update"
git push
quarto publish gh-pages

## 4. Instructor gate (when instructor content is added)
npm install -g staticrypt
staticrypt _site/instructor.html -p "<ACCESS-CODE-FROM-IM>" --short
