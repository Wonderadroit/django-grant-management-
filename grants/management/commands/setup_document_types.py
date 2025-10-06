from django.core.management.base import BaseCommand
from grants.models import DocumentType

class Command(BaseCommand):
    help = 'Create default document types for grant applications'

    def handle(self, *args, **options):
        document_types = [
            {
                'name': 'Government ID',
                'description': 'Valid government-issued photo identification (driver\'s license, passport, state ID)',
                'required': True,
                'display_order': 1,
                'allowed_extensions': 'pdf,jpg,jpeg,png'
            },
            {
                'name': 'Proof of Income',
                'description': 'Recent tax returns, pay stubs, or benefit statements showing current financial status',
                'required': True,
                'display_order': 2,
                'allowed_extensions': 'pdf,doc,docx,jpg,jpeg,png'
            },
            {
                'name': 'Bank Statements',
                'description': 'Recent bank statements (last 3 months) showing current financial status',
                'required': True,
                'display_order': 3,
                'allowed_extensions': 'pdf,jpg,jpeg,png'
            },
            {
                'name': 'Project Proposal',
                'description': 'Detailed project proposal document with timeline and objectives',
                'required': True,
                'display_order': 4,
                'allowed_extensions': 'pdf,doc,docx'
            },
            {
                'name': 'Budget Documentation',
                'description': 'Detailed budget breakdown and cost estimates for your project',
                'required': True,
                'display_order': 5,
                'allowed_extensions': 'pdf,doc,docx'
            },
            {
                'name': 'Reference Letters',
                'description': 'Letters of recommendation or support from community members, employers, or other organizations',
                'required': False,
                'display_order': 6,
                'allowed_extensions': 'pdf,doc,docx,jpg,jpeg,png'
            },
            {
                'name': 'Medical Documentation',
                'description': 'Medical records, bills, or documentation (for healthcare-related requests)',
                'required': False,
                'display_order': 7,
                'allowed_extensions': 'pdf,jpg,jpeg,png'
            },
            {
                'name': 'Educational Records',
                'description': 'Transcripts, enrollment verification, or educational certificates (for education-related requests)',
                'required': False,
                'display_order': 8,
                'allowed_extensions': 'pdf,jpg,jpeg,png'
            },
            {
                'name': 'Business Registration',
                'description': 'Business license, registration, or incorporation documents (for business-related requests)',
                'required': False,
                'display_order': 9,
                'allowed_extensions': 'pdf,jpg,jpeg,png'
            },
            {
                'name': 'Additional Supporting Documents',
                'description': 'Any additional documents that support your application',
                'required': False,
                'display_order': 10,
                'allowed_extensions': 'pdf,doc,docx,jpg,jpeg,png,txt'
            }
        ]

        created_count = 0
        for doc_type_data in document_types:
            doc_type, created = DocumentType.objects.get_or_create(
                name=doc_type_data['name'],
                defaults=doc_type_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created document type: {doc_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Document type already exists: {doc_type.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} document types')
        )