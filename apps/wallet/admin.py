import csv
from decimal import Decimal
from django.contrib import admin
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django import forms
from .models import Wallet, Transaction, DepositRequest, WithdrawRequest
from core.services import WalletService


class AdminCreditForm(forms.Form):
    amount = forms.DecimalField(min_value=Decimal('0.01'), max_digits=12, decimal_places=2)
    description = forms.CharField(max_length=255, required=False)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    actions = ['export_csv']

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('<uuid:wallet_id>/credit/', self.admin_site.admin_view(self.credit_view),
                 name='wallet_admin_credit'),
        ]
        return custom + urls

    def credit_view(self, request, wallet_id):
        from django.shortcuts import render, redirect, get_object_or_404
        wallet = get_object_or_404(Wallet, pk=wallet_id)
        if request.method == 'POST':
            form = AdminCreditForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data['amount']
                desc = form.cleaned_data['description'] or f'Admin credit by {request.user.username}'
                WalletService.credit(
                    wallet, amount,
                    reference=f'ADMIN_{wallet_id}_{Transaction.objects.count()}',
                    description=desc,
                )
                messages.success(request, f'Credited {amount} to {wallet.user.username}')
                return redirect('..')
        else:
            form = AdminCreditForm()
        return render(request, 'admin/wallet/credit_form.html', {
            'form': form, 'wallet': wallet,
            'title': f'Credit wallet: {wallet.user.username}'
        })

    @admin.action(description='Export wallets as CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="wallets.csv"'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Balance', 'Updated'])
        for w in queryset.select_related('user'):
            writer.writerow([w.user.username, w.user.email, w.balance, w.updated_at])
        return response


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'tx_type', 'amount', 'balance_after', 'category',
                    'reference', 'created_at']
    list_filter = ['tx_type', 'category', 'created_at']
    search_fields = ['wallet__user__username', 'reference', 'description']
    readonly_fields = [f.name for f in Transaction._meta.fields]
    ordering = ['-created_at']
    actions = ['export_csv']

    @admin.action(description='Export transactions as CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(['User', 'Type', 'Amount', 'Balance After', 'Category',
                         'Reference', 'Description', 'Created At'])
        for tx in queryset.select_related('wallet__user'):
            writer.writerow([tx.wallet.user.username, tx.tx_type, tx.amount,
                             tx.balance_after, tx.category, tx.reference,
                             tx.description, tx.created_at])
        return response


# ─── Deposit Request Admin ─────────────────────────────────────────────────

class DepositRequestAdminForm(forms.ModelForm):
    class Meta:
        model = DepositRequest
        fields = ['status', 'admin_note']


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'username', 'amount', 'utr_number',
        'status', 'created_at', 'reviewed_by', 'reviewed_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['wallet__user__username', 'utr_number', 'upi_id_used']
    readonly_fields = ['id', 'wallet', 'amount', 'utr_number', 'upi_id_used',
                       'created_at', 'updated_at', 'reviewed_by', 'reviewed_at']
    ordering = ['-created_at']
    actions = ['approve_deposits', 'reject_deposits', 'export_csv']

    # Only editable fields for admin
    fields = [
        'id', 'wallet', 'amount', 'utr_number', 'upi_id_used',
        'status', 'admin_note', 'reviewed_by', 'reviewed_at',
        'created_at', 'updated_at',
    ]

    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'

    def username(self, obj):
        return obj.wallet.user.username
    username.short_description = 'User'
    username.admin_order_field = 'wallet__user__username'

    def save_model(self, request, obj, form, change):
        """Auto-approve: credit wallet when status changed to APPROVED."""
        if change:
            old = DepositRequest.objects.get(pk=obj.pk)
            if old.status != 'APPROVED' and obj.status == 'APPROVED':
                self._do_approve(request, obj)
            elif old.status != 'REJECTED' and obj.status == 'REJECTED':
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def _do_approve(self, request, deposit):
        """Credit the wallet and mark reviewed."""
        try:
            WalletService.credit(
                deposit.wallet,
                deposit.amount,
                reference=f'DEPOSIT_{deposit.id}',
                description=f'Deposit approved — UTR: {deposit.utr_number}',
                category='DEPOSIT',
            )
            deposit.reviewed_by = request.user
            deposit.reviewed_at = timezone.now()
            messages.success(request, f'✅ Credited ₹{deposit.amount} to {deposit.wallet.user.username}')
        except Exception as e:
            messages.error(request, f'Error crediting wallet: {e}')

    @admin.action(description='✅ Approve selected deposits & credit wallets')
    def approve_deposits(self, request, queryset):
        approved = 0
        for deposit in queryset.filter(status='PENDING'):
            self._do_approve(request, deposit)
            deposit.status = 'APPROVED'
            deposit.save()
            approved += 1
        if approved:
            messages.success(request, f'Approved {approved} deposit(s).')
        else:
            messages.warning(request, 'No PENDING deposits selected.')

    @admin.action(description='❌ Reject selected deposits')
    def reject_deposits(self, request, queryset):
        rejected = queryset.filter(status='PENDING').update(
            status='REJECTED',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        messages.success(request, f'Rejected {rejected} deposit(s).')

    @admin.action(description='Export as CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="deposit_requests.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Amount', 'UTR', 'UPI Used', 'Status',
                         'Admin Note', 'Reviewed By', 'Created At'])
        for d in queryset.select_related('wallet__user', 'reviewed_by'):
            writer.writerow([
                d.id, d.wallet.user.username, d.amount, d.utr_number,
                d.upi_id_used, d.status, d.admin_note,
                d.reviewed_by.username if d.reviewed_by else '',
                d.created_at,
            ])
        return response


# ─── Withdraw Request Admin ────────────────────────────────────────────────

@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'username', 'amount', 'upi_id',
        'status', 'created_at', 'reviewed_by', 'reviewed_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['wallet__user__username', 'upi_id']
    readonly_fields = ['id', 'wallet', 'amount', 'upi_id',
                       'created_at', 'updated_at', 'reviewed_by', 'reviewed_at']
    ordering = ['-created_at']
    actions = ['approve_withdrawals', 'reject_withdrawals', 'export_csv']

    fields = [
        'id', 'wallet', 'amount', 'upi_id',
        'status', 'admin_note', 'reviewed_by', 'reviewed_at',
        'created_at', 'updated_at',
    ]

    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'

    def username(self, obj):
        return obj.wallet.user.username
    username.short_description = 'User'
    username.admin_order_field = 'wallet__user__username'

    def save_model(self, request, obj, form, change):
        """On rejection: refund the held amount back to wallet."""
        if change:
            old = WithdrawRequest.objects.get(pk=obj.pk)
            if old.status == 'PENDING' and obj.status == 'REJECTED':
                self._do_refund(request, obj)
            if old.status != obj.status:
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def _do_refund(self, request, withdrawal):
        """Refund the deducted amount back if rejected."""
        try:
            WalletService.credit(
                withdrawal.wallet,
                withdrawal.amount,
                reference=f'WD_REFUND_{withdrawal.id}',
                description=f'Withdrawal rejected — refund to wallet',
                category='BET_REFUND',
            )
            messages.success(request, f'↩️ Refunded ₹{withdrawal.amount} to {withdrawal.wallet.user.username}')
        except Exception as e:
            messages.error(request, f'Error refunding wallet: {e}')

    @admin.action(description='✅ Approve selected withdrawals (money sent externally)')
    def approve_withdrawals(self, request, queryset):
        approved = 0
        for wd in queryset.filter(status='PENDING'):
            wd.status = 'APPROVED'
            wd.reviewed_by = request.user
            wd.reviewed_at = timezone.now()
            wd.save()
            approved += 1
            messages.success(request,
                f'✅ Approved ₹{wd.amount} withdrawal to {wd.upi_id} for {wd.wallet.user.username}. '
                f'Please send manually via your UPI app.')
        if not approved:
            messages.warning(request, 'No PENDING withdrawals selected.')

    @admin.action(description='❌ Reject selected withdrawals (refunds wallet)')
    def reject_withdrawals(self, request, queryset):
        rejected = 0
        for wd in queryset.filter(status='PENDING'):
            self._do_refund(request, wd)
            wd.status = 'REJECTED'
            wd.reviewed_by = request.user
            wd.reviewed_at = timezone.now()
            wd.save()
            rejected += 1
        messages.success(request, f'Rejected & refunded {rejected} withdrawal(s).')

    @admin.action(description='Export as CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="withdraw_requests.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Amount', 'UPI ID', 'Status',
                         'Admin Note', 'Reviewed By', 'Created At'])
        for w in queryset.select_related('wallet__user', 'reviewed_by'):
            writer.writerow([
                w.id, w.wallet.user.username, w.amount, w.upi_id,
                w.status, w.admin_note,
                w.reviewed_by.username if w.reviewed_by else '',
                w.created_at,
            ])
        return response