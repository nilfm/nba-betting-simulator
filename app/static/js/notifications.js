Vue.use(VueToast);

var notifications = new Vue({
    el: "#notifications",
    methods: {
        add: function(notif) {
            this.$toast.open({
                message: notif.message,
                type: notif.type,
                duration: 5000,
                dismissible: true
            })
        },
        add_success: function(message) {
            this.$toast.open({
                message: message,
                type: 'success',
                duration: 5000,
                dismissible: true
            })
        },
        add_warning: function(message) {
            this.$toast.open({
                message: message,
                type: 'warning',
                duration: 5000,
                dismissible: true
            })
        },
        add_error: function(message) {
            this.$toast.open({
                message: message,
                type: 'error',
                duration: 5000,
                dismissible: true
            })
        }
    }
})
