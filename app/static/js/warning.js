function danger_warning() {
    if (confirm("This action is irreversible. Are you sure?")) {
        this.form.submit();
        return true;
    }
    return false;
}
