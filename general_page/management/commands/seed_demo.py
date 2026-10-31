"""Seed an empty local database with fictional, reproducible product examples."""
import json
import os
from pathlib import Path
import secrets
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from user_blog.models import Comment, Post
from user_page.models import Knowledge
from user_topics.models import Topic
from apis.like_api.services import to_like
import user_topics.servisec  # Register the Topic -> Category creation signal.


ARTICLES = [
    ('A learning journal that grows with you', 'Development', ['Learning systems', 'Заметки'],
     'Turn a single useful observation into a connected collection of ideas.',
     'Start small', 'A good learning journal begins with a concrete question. Write down what you tried, what happened, and what you would change next time.',
     'Connect the ideas', 'Give the article a home in a stream, then attach the topics that help you find it again. A note about a database experiment can also belong to a broader learning practice.',
     'Make room for discussion', 'A reply can challenge an assumption or suggest the next experiment. Keeping that exchange beside the article makes the reasoning easier to revisit.'),
    ('Why database relationships matter', 'Development', ['Databases', 'Learning systems'],
     'Model the relationship first; the interface becomes easier to reason about.',
     'One home, several connections', 'An article has a primary stream but can belong to more than one topic. A many-to-many relationship keeps these connections explicit without duplicating the article.',
     'Separate structure from presentation', 'The same article can appear in a personal blog, a topic gallery, and the public feed. Each view answers a different question using the same stored content.',
     'Ask a useful question', 'Before adding a field, ask which operation needs it. Relationships should explain the product, not merely mirror the layout of one screen.'),
    ('Reading an API as a product contract', 'Development', ['Databases', 'Заметки'],
     'A small API is easier to trust when its permissions match its purpose.',
     'Name the capability', 'A feed reads articles. A like action records a reaction. Keeping these capabilities distinct makes the interface and its permissions easier to understand.',
     'Test two perspectives', 'Try the same operation as the author and as another reader. A successful request for one person does not imply that the other person should be allowed to make it.',
     'Keep the feedback close', 'Document the expected behavior beside a focused test. Future changes can then preserve the original intent without relying on memory.'),
    ('The opportunity cost of an afternoon', 'Economics', ['Decision making', 'Learning systems'],
     'Time spent on one project is time unavailable to another: make that tradeoff visible.',
     'List the alternatives', 'An afternoon can go toward reading, building, or resting. Opportunity cost is the value of the next-best alternative, not simply the money spent.',
     'Use a small experiment', 'When the outcome is uncertain, a short experiment can reveal more than a long debate. Choose a time limit and write down what evidence would change your mind.',
     'Review the choice', 'Compare your expectations with the result. A useful decision journal records the information available at the time, rather than judging only the eventual outcome.'),
    ('Compound learning, one week at a time', 'Economics', ['Decision making', 'Заметки'],
     'A weekly review can turn scattered effort into an improving system.',
     'Collect the signals', 'Choose three notes from the week: something learned, something misunderstood, and a question worth exploring. Link them to the relevant topics.',
     'Revisit instead of restart', 'Returning to an earlier explanation reveals gaps that were invisible when you first wrote it. Improving an existing article is often more valuable than starting another.',
     'Share a specific question', 'Ask a reader to inspect one claim or example. A focused discussion creates a useful next step for both people.'),
    ('From a prototype to a shared notebook', 'Development', ['Learning systems', 'Databases'],
     'A working notebook becomes more valuable when another person can follow the reasoning.',
     'Show the complete path', 'A useful prototype lets someone move from a stream to a topic, open an article, and join a discussion. The connections matter as much as any individual screen.',
     'Leave evidence', 'Screenshots, examples, and small tests help the next reader reproduce the result. Explain the constraints as carefully as the happy path.',
     'Keep ownership clear', 'Publishing and maintaining software are different stages. Preserve the original work while making installation and its current limitations understandable.'),
]


def make_cover(path, index):
    path.parent.mkdir(parents=True, exist_ok=True)
    palettes = [('#14243a', '#60d5c2'), ('#25213c', '#bd9bea'), ('#21372e', '#bee68c'),
                ('#442a22', '#f2b071'), ('#17333c', '#74c8eb'), ('#352c43', '#ed94b5')]
    background, accent = palettes[index % len(palettes)]
    image = Image.new('RGB', (960, 600), background)
    draw = ImageDraw.Draw(image)
    for i in range(5):
        x = 80 + i * 170
        y = 100 + ((i + index) % 3) * 90
        draw.rounded_rectangle((x, y, x + 120, y + 180), radius=20, fill=accent)
        if i:
            draw.line((x - 50, 300, x, y + 90), fill='#ffffff', width=4)
    draw.text((40, 550), 'STUDYFLUX / DEMO {:02d}'.format(index + 1), fill='#ffffff')
    image.save(path)


class Command(BaseCommand):
    help = 'Populate an empty local database with fictional demo content (never resets existing users).'

    def handle(self, *args, **options):
        if not settings.DEBUG or os.environ.get('DJANGO_SETTINGS_MODULE') != 'my_portfolio.settings_local':
            raise CommandError('Demo seeding is only available with local development settings.')
        if User.objects.exists():
            self.stdout.write('Existing accounts detected; demo data left unchanged.')
            return
        runtime = Path(os.environ['STUDYFLUX_RUNTIME'])
        runtime.mkdir(parents=True, exist_ok=True)
        credentials_path = runtime / 'demo-credentials.json'
        if credentials_path.exists():
            credentials = json.loads(credentials_path.read_text())
        else:
            credentials = {'username': 'demo', 'password': secrets.token_urlsafe(18)}
            fd = os.open(str(credentials_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as file:
                json.dump(credentials, file)
        media = Path(settings.MEDIA_ROOT)
        # The four built-in stream covers also support normal user registration.
        (media / 'portfolio').mkdir(parents=True, exist_ok=True)
        for source in (Path(settings.BASE_DIR) / 'my_portfolio/static/img/portfolio').glob('*.jpg'):
            target = media / 'portfolio' / source.name
            if not target.exists():
                shutil.copyfile(source, target)
        with transaction.atomic():
            author = User.objects.create_user('demo', 'demo@example.invalid', credentials['password'], first_name='Alex')
            reader = User.objects.create_user('demo-reader', 'reader@example.invalid', secrets.token_urlsafe(24), first_name='Sam')
            streams = {}
            for name, image in [('Development', '2.jpg'), ('Economics', '3.jpg')]:
                streams[name] = Knowledge.objects.create(user=author, name=name, image='portfolio/' + image)
            topics = {}
            for title, stream in [('Learning systems', 'Development'), ('Databases', 'Development'), ('Заметки', 'Development'), ('Decision making', 'Economics')]:
                topics[title] = Topic.objects.create(user=author, knowledge=streams[stream], title=title, description='Demo notes about ' + title)
            reader_stream = Knowledge.objects.create(user=reader, name='Development', image='portfolio/2.jpg')
            posts = []
            for index, article in enumerate(ARTICLES):
                title, stream, tags, header, h1, p1, h2, p2, h3, p3 = article
                image_name = 'demo/covers/{:02d}.png'.format(index + 1)
                make_cover(media / image_name, index)
                body = '<h2>{}</h2><p>{}</p><h2>{}</h2><p>{}</p><h2>{}</h2><p>{}</p>'.format(h1, p1, h2, p2, h3, p3)
                body += '<p><img src="{}{}" alt="Abstract connected notes" style="max-width:100%"></p>'.format(settings.MEDIA_URL, image_name)
                owner = reader if index == 5 else author
                post = Post.objects.create(user=owner, knowledge_field=reader_stream if index == 5 else streams[stream], title=title, header=header, body=body, image=image_name, pinned=index < 4)
                if owner == author:
                    post.categories.set([topics[tag].category for tag in tags])
                else:
                    topic = Topic.objects.create(user=reader, knowledge=reader_stream, title='Learning systems', description='Notes from a second reader')
                    post.categories.add(topic.category)
                to_like(post, reader)
                if index % 2 == 0:
                    to_like(post, author)
                posts.append(post)
            root = Comment.objects.create(post=posts[0], user=reader, body='How do you decide whether a note needs a new topic?', path=[])
            root.path = [root.pk]
            root.save()
            reply = Comment.objects.create(post=posts[0], user=author, body='I wait until several notes share the same question. One article can belong to both topics.', path=[])
            reply.path = root.path + [reply.pk]
            reply.save()
            nested = Comment.objects.create(post=posts[0], user=reader, body='That makes sense: let the connections emerge before adding more structure.', path=[])
            nested.path = reply.path + [nested.pk]
            nested.save()
            comment = Comment.objects.create(post=posts[0], user=author, body='Try the topic gallery to explore these connections visually.', path=[])
            comment.path = [comment.pk]
            comment.save()
        self.stdout.write(self.style.SUCCESS('Created 2 demo users, 6 articles, topics, likes and threaded comments.'))
