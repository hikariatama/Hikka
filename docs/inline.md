# Hikka.inline Docs [beta]
## Документация будет пополняться
### Приготовлено @hikariatama с любовью и заботой :･ﾟ✧(ꈍᴗꈍ)✧･ﾟ:
Для каждого модуля по умолчанию доступен атрибут `inline`. Все операции выполняются через него.

## Скопы
Модули, использующие **любые** возможности этого режима должны содержать скопу (комментарий):
`# scope: inline`
Если вы **не обрабатываете возможность** использования модуля на классическом FTG (`if hasattr(self, 'inline')`), необходимо также указать скоп (не обрабатывается юзерботом, но помогает анализаторам модулей):
`# scope: hikka_only`
Если в модуле требуется **определенная** версия Hikka, для этого тоже есть скоп:
`# scope: hikka_min 1.0.0`

## Создание формы
Для создания кнопок в сообщении, используй встроенный [менеджер форм](https://github.com/hikariatama/Hikka/blob/master/hikka/inline/form.py#L40):

### Референс:
```python
async def form(
    self,
    text: str,
    message: Union[Message, int],
    reply_markup: List[List[dict]] = None,
    force_me: bool = True,
    always_allow: Union[List[list], None] = None,
    ttl: Union[int, bool] = False,
    on_unload: Union[FunctionType, None] = None,
) -> Union[str, bool]:
```
### Пример:
```python
await self.inline.form(
    text="📊 Poll Hikka vs. FTG\n🌘 Hikka: No votes\n😔 FTG: No votes",
    message=message,
    reply_markup=[
        [
            {
                "text": "Hikka",
                "callback": self.vote,
                "args": [False]
            }
        ],
        [
            {
                "text": "FTG",
                "callback": self.vote,
                "args": [True]
            }
        ],
    ],
    force_me=False,  # optional: Allow other users to access form (all)
    always_allow=[659800858],  # optional: Permit users with IDs
    ttl=30,  # optional: Time to live of form in seconds
)
```
![Без имени-1](https://user-images.githubusercontent.com/36935426/157850552-ff489e8e-3f64-4139-b1d6-b95c430707c0.png)

Примеры возможных кнопок разных типов:

### Кнопка с обработчиком в виде функции:
```python
{
    "text": "Button with function",
    "callback": self.callback_handler,
    "args": (arg1, ),  # optional arguments passed to callback
    "kwargs": {"arg1name": "arg1"},  # optional kwargs passed to callback
}
```
### Кнопка с кастомным обработчиком (button_callback_handler):
```python
{
    "text": "Button with custom payload",
    "data": "custom_payload",
}
```
### Кнопка со ссылкой:
```python
{
    "text": "URL Button",
    "url": "https://example.com",
}
```
### Кнопка, которая просит пользователя ввести значение:
```python
{
    "text": "✍️ Enter value",
    "input": "✍️ Enter new configuration value for this option",
    "handler": self.input_handler,
    "args": (arg1, ),  # optional arguments passed to callback
    "kwargs": {"arg1name": "arg1"},  # optional kwargs passed to callback
}
```

При создании, форма возвращает `False`, если произошла какая-то ошибка, либо строку с `form_uid`.

> ⚠️ **При возникновении ошибки при создании формы, exception не поднимается!**

## Галерея
В Hikka доступны [inline-галереи](https://github.com/hikariatama/Hikka/blob/master/hikka/inline/gallery.py#L42). Вызвать ее очень просто:

### Референс:
```python
async def gallery(
    self,
    message: Union[Message, int],
    next_handler: Union[FunctionType, List[str]],
    caption: Union[str, FunctionType] = "",
    *,
    force_me: bool = True,
    always_allow: Union[list, None] = None,
    ttl: Union[int, bool] = False,
    on_unload: Union[FunctionType, None] = None,
    preload: Union[bool, int] = False,
    gif: bool = False,
    _reattempt: bool = False,
) -> Union[bool, str]:
```
### Пример
```python
def generate_caption() -> str:
    return random.choice(["Да", "Нет"])

async def photo() -> str:
    return (await utils.run_sync(requests.get, "https://api.catboys.com/img")).json()["url"]

await self.inline.gallery(
    message=message,
    next_handler=photo,
    caption=generate_caption,
)
```
Здесь `generate_caption` - функция, возвращающая описание фото
`photo` - Асинхронная функция, возвращая следующую картинку (при нажатии на кнопку Next)
> Вместо функции `generate_caption` можно передать обычную строку или лямбда-функцию
## Инлайн-галерея
Если ты хочешь, чтобы пользователь мог вызвать галерею через инлайн-запрос к боту (@hikka_xxxxxx_bot), используй (встроенные галереи)[https://github.com/hikariatama/Hikka/blob/master/hikka/inline/gallery.py#L253]

### Референс:
```python
async def query_gallery(
    self,
    query: InlineQuery,
    items: List[dict],
    *,
    force_me: bool = True,
    always_allow: Union[list, None] = None,
) -> None:
```
### Пример
```python
async def catboy_inline_handler(self, query: InlineQuery) -> None:
    """
    Send Catboys
    """
    await self.inline.query_gallery(
        query,
        [
            {
                "title": "🌘 Catboy",
                "description": "Send catboy photo",
                "next_handler": photo,
                "thumb_handler": photo,  # Optional
                "caption": lambda: f"<i>Enjoy! {utils.escape_html(utils.ascii_face())}</i>",  # Optional
                # Because of ^ this lambda, face will be generated every time the photo is switched

                # "caption": f"<i>Enjoy! {utils.escape_html(utils.ascii_face())}</i>",
                # If you make it without lambda ^, it will be generated once
            }
        ],
    )

```

## Обработка нажатий (вариант 1)
Есть несколько вариантов обработки нажатий. Если ты хочешь, чтобы кнопка жила **бесконечное** количество времени, ты можешь использовать опцию `data`.
```python
chat_id = 123123
user_id = 321321
...
reply_markup=[
    [
        {
            "text": "Unban",
            "data": f"ub/{chat_id}/{user_id}",
        }
    ]
],
...
```
В такие кнопки нельзя передавать функцию, поэтому нажатия на них нужно обрабатывать вручную. Пример обработчика:
```python
async def actions_callback_handler(self, call: CallbackQuery) -> None:
    """
        Handles unmute\\unban button clicks
        @allow: all
    """
    if not re.match(r"[fbmudw]{1,3}\/[-0-9]+\/[-#0-9]+", call.data):
        return
```
Вместо проверки регулярным выражением, ты можешь проверять вручную. Например:
```python
if call.data.split("/")[0] not in {'ub', 'un', 'ufm'}:
    return
```
В таком случае, пайлоад должен иметь вид:
```
ub/...
un/...
ufm/...
```
## Обработка нажатий (вариант 2)
В случае, если ты передаешь в кнопку `callback` тебе не нужно вручную создавать **валидатор пайлоада**.

Пример, в котором в обработчик передается один позиционный аргумент:
```python
async def _process_click_ai(self, call: CallbackQuery, arg1: str) -> None:
    # Do some stuff
```
В этом случае в `call` доступно еще несколько атрибутов у аргумента `call`:
```python
await call.unload()  # Unload form from memory

await call.delete()  # Unload form from memory and delete message

await call.edit(
    text="Some new text",
    reply_markup=[
        [
            {
                "text": "New Button",
                "url": "https://ya.ru"
            }
        ]
    ],  # optional: Change buttons in message. If not specified, buttons will be removed
    disable_web_page_preview=True,  # optional: Disable link preview
    always_allow=[659800858],  # optional: Change allowed users
    force_me=False,  # optional: Change button privacy mode
)

call.form  # optional: Contains info about form
```
> ⚠️ **Эти атрибуты недоступны в обычном обработчике.** В этом случае нужно пользоваться средствами aiogram и редактировать сообщение вручную, используя `await self.inline._bot.edit_message_text`!

## Inline команды (@bot ...)
Для обработки инлайн команд Hikka использует обработчики, созданные по шаблону, наподобие командам.
```python
from ..inline import InlineQuery

async def <name>_inline_handler(self, query: InlineQuery) -> None:
    # Process request
```
Внутри объекта query доступен атрибут args, который содержит в себе текст, указанный после команды (@bot <name> **some text here**)

Отвечать на этот запрос необходимо так же, как и в `aiogram`. Для подробной информации, читай **их документацию**.

Для примера привожу кусок кода из `inline.py`, отвечающий за вывод всех доступных команд:
```python
await query.answer(
    [
        InlineQueryResultArticle(
            id=utils.rand(20),
            title="Show available inline commands",
            description=f"You have {len(_help.splitlines())} available command(-s)",
            input_message_content=InputTextMessageContent(
                f"<b>ℹ️ Available inline commands:</b>\n\n{_help}",
                "HTML",
                disable_web_page_preview=True,
            ),
            thumb_url="https://img.icons8.com/fluency/50/000000/info-squared.png",
            thumb_width=128,
            thumb_height=128,
        )
    ],
    cache_time=0,
)
```
В каждом из таких ответов необходимо указывать идентификатор. Чтобы не усложнять жизнь, можно импортировать генератор из встроенного модуля:
```python
from .. import utils
```
Затем можно указывать rand(20) в значении атрибута id

### Полезные сокращения

`await query.e400()` - Неверные аргументы
`await query.e403()` - Недостаточно прав для доступа к ресурсу
`await query.e404()` - Требуемый результат не найден
`await query.e426()` - Необходимо обновление юзербота
`await query.e500()` - Ошибка модуля. Смотри логи

### Правильный ответ на Inline запрос

Вместо того, чтобы вручную вызывать `query.answer`, можно просто вернуть словарь с нужным ответом. Либо список из подобных словарей

- `{"message": "<b>Текст сообщения</b>", "title": "Текстовый ответ"}` 
- `{"photo": "https://i.imgur.com/hZIyI7v.jpeg", "title": "Фотография"}`
- `{"video": "https://x0.at/wWN9.mp4", "title": "Видео"}`
- `{"file": "https://x0.at/f7ps.pdf", "mime_type": "application/pdf", "title": "Документ"}`
- `{"gif": "https://x0.at/Sey-.mp4", "title": "GIF-ка"}`
