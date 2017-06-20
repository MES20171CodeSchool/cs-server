from html import escape

from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from codeschool import models, panels
from codeschool.core.models import ProgrammingLanguage
from codeschool.questions.coding_io.models import CodingIoQuestion
from codeschool.utils.string import md5hash


class AnswerKeySource(models.Model):
    """

    """

    NULL_SOURCE_HASH = md5hash('')

    validated = models.BooleanField(
        _('is validated?'),
        default=False,
        help_text=_('Verify if the answer key source is validated')
    )
    source = models.TextField(
        _('answer source code'),
        blank=True,
        help_text=_(
            'Source code for the correct answer in the given programming '
            'language.'
        ),
    )
    error_message = models.TextField(
        _('error message'),
        blank=True,
        help_text=_(
            'If an error is found on post-validation, an error message is '
            'stored in here.'
        )
    )
    source_hash = models.CharField(
        max_length=32,
        default=NULL_SOURCE_HASH,
        help_text=_('Hash computed from the reference source'),
    )

    def set_error_message(self, message):
        """
        Saves error message.
        """

        try:
            self.error_message = message.__html__()
        except AttributeError:
            self.error_message = escape(message)

    def clean(self, language):
        try:
            check_syntax(self.source, lang=language.ejudge_ref())
        except SyntaxError as ex:
            msg = _('Invalid syntax: %(msg)') % {'msg': str(ex)}
            raise ValidationError({'source': msg})
        super().clean()

        # Validation is async:
        #
        # We first run basic validations in the foreground and later attempt
        # at more detailed validations that requires us to run source code (and
        # thus possibly wait a long time).
        #
        # If this later validation step encounters errors, it saves them on
        # the model instance. The next time the model runs, we can re-raise
        # them on the interface. The user has an option to bypass these checks.
        # Changing the code or the iospec entries should expire these
        # errors.
        if self.error_message and not self.is_ignoring_validation_errors():
            raise ValidationError({'source': mark_safe(self.error_message)})

    def save(self, *args, **kwargs):
        self.source_hash = md5hash(self.source)
        super().save(*args, **kwargs)

    def has_changed_source(self):
        """
        Return True if source is not consistent with its hash.
        """

        return self.source_hash != md5hash(self.source)

    # Wagtail admin
    panels = [
        panels.FieldPanel('source'),
    ]

    class Meta:
        verbose_name = _('answer key source')
        verbose_name_plural = _('answer keys source')


class AnswerKey(models.Model):
    """
    Represents an answer to some question given in some specific computer
    language plus the placeholder text that should be displayed.
    """

    class ValidationError(Exception):
        pass

    class Meta:
        verbose_name = _('answer key')
        verbose_name_plural = _('answer keys')
        unique_together = [('question', 'language')]

    question = models.ParentalKey(
        CodingIoQuestion,
        related_name='answers'
    )
    language = models.ForeignKey(
        ProgrammingLanguage,
        related_name='+',
    )
    placeholder = models.TextField(
        _('placeholder source code'),
        blank=True,
        help_text=_(
            'This optional field controls which code should be placed in '
            'the source code editor when a question is opened. This is '
            'useful to put boilerplate or even a full program that the '
            'student should modify. It is possible to configure a global '
            'per-language boilerplate and leave this field blank.'
        ),
    )
    answerKeySource = models.OneToOneField(
        AnswerKeySource,
        on_delete=models.CASCADE,
        editable=False
    )

    def __repr__(self):
        return '<AnswerKey: %s>' % self

    def __str__(self):
        try:
            title = self.question.title
        except:
            title = '<untitled>'
        return '%s (%s)' % (title, self.language)

    def is_ignoring_validation_errors(self):
        """
        True to ignore errors found in post-validation.
        """

        return self.question.ignore_validation_errors

    def single_reference(self, source):
        """
        Return True if it is the only answer key in the set that defines a
        source attribute.
        """

        if not self.source:
            return False

        try:
            return self.question.answers.has_program().get() == self
        except self.DoesNotExist:
            return False

    # Wagtail admin
    panels = [
        panels.FieldPanel('language'),
        panels.FieldPanel('placeholder'),
    ]


def check_syntax(source, lang):
    """
    Raises a SyntaxError if source code is invalid in the given language.
    """

    if lang == 'python':
        compile(source, '<input>', 'exec')
    else:
        # FIXME: implement this in ejudge.
        pass
