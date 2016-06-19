from __future__ import absolute_import
from webserver.testing import ServerTestCase
from db import dataset, user
from flask import url_for
import json
import mock
import datetime


class DatasetsViewsTestCase(ServerTestCase):

    def setUp(self):
        super(DatasetsViewsTestCase, self).setUp()

        self.test_user_mb_name = "tester"
        self.test_user_id = user.create(self.test_user_mb_name)

        self.test_uuid = "123e4567-e89b-12d3-a456-426655440000"
        self.test_data = {
            "name": "Test",
            "description": "",
            "classes": [],
            "public": True,
        }

    def test_view(self):
        resp = self.client.get(url_for("datasets.view", id=self.test_uuid))
        self.assert404(resp)

        dataset_id = dataset.create_from_dict(self.test_data, author_id=self.test_user_id)
        resp = self.client.get(url_for("datasets.view", id=dataset_id))
        self.assert200(resp)

    def test_view_json(self):
        resp = self.client.get(url_for("datasets.view_json", id=self.test_uuid))
        self.assert404(resp)

        dataset_id = dataset.create_from_dict(self.test_data, author_id=self.test_user_id)
        resp = self.client.get(url_for("datasets.view_json", id=dataset_id))
        self.assert200(resp)

    def test_create(self):
        resp = self.client.get(url_for("datasets.create"))
        self.assertStatus(resp, 302)

        resp = self.client.post(
            url_for("datasets.create"),
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.test_data),
        )
        self.assertStatus(resp, 302)

        # With logged in user
        self.temporary_login(self.test_user_id)

        resp = self.client.get(url_for("datasets.create"))
        self.assert200(resp)

        resp = self.client.post(
            url_for("datasets.create"),
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.test_data),
        )
        self.assert200(resp)
        self.assertTrue(len(dataset.get_by_user_id(self.test_user_id)) == 1)

    def test_edit(self):
        # Should redirect to login page even if trying to edit dataset that
        # doesn't exist.
        resp = self.client.get(url_for("datasets.edit", dataset_id=self.test_uuid))
        self.assertStatus(resp, 302)

        dataset_id = dataset.create_from_dict(self.test_data, author_id=self.test_user_id)

        # Trying to edit without login
        resp = self.client.get(url_for("datasets.edit", dataset_id=dataset_id))
        self.assertStatus(resp, 302)
        resp = self.client.post(
            url_for("datasets.edit", dataset_id=dataset_id),
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.test_data),
        )
        self.assertStatus(resp, 302)

        # Editing using another user
        another_user_id = user.create("another_tester")
        self.temporary_login(another_user_id)
        resp = self.client.get(url_for("datasets.edit", dataset_id=dataset_id))
        self.assert401(resp)
        resp = self.client.post(
            url_for("datasets.edit", dataset_id=dataset_id),
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.test_data),
        )
        self.assert401(resp)

        # Editing properly
        self.temporary_login(self.test_user_id)
        resp = self.client.get(url_for("datasets.edit", dataset_id=dataset_id))
        self.assert200(resp)
        resp = self.client.post(
            url_for("datasets.edit", dataset_id=dataset_id),
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.test_data),
        )
        self.assert200(resp)

    def test_delete(self):
        # Should redirect to login page even if trying to delete dataset that
        # doesn't exist.
        resp = self.client.get(url_for("datasets.delete", dataset_id=self.test_uuid))
        self.assertStatus(resp, 302)

        dataset_id = dataset.create_from_dict(self.test_data, author_id=self.test_user_id)

        # Trying to delete without login
        resp = self.client.get(url_for("datasets.delete", dataset_id=dataset_id))
        self.assertStatus(resp, 302)
        resp = self.client.post(url_for("datasets.delete", dataset_id=dataset_id))
        self.assertStatus(resp, 302)
        self.assertTrue(len(dataset.get_by_user_id(self.test_user_id)) == 1)

        # Deleting using another user
        another_user_id = user.create("another_tester")
        self.temporary_login(another_user_id)
        resp = self.client.get(url_for("datasets.delete", dataset_id=dataset_id))
        self.assert401(resp)
        resp = self.client.post(url_for("datasets.delete", dataset_id=dataset_id))
        self.assert401(resp)
        self.assertTrue(len(dataset.get_by_user_id(self.test_user_id)) == 1)

        # Editing properly
        self.temporary_login(self.test_user_id)
        resp = self.client.get(url_for("datasets.delete", dataset_id=dataset_id))
        self.assert200(resp)
        resp = self.client.post(url_for("datasets.delete", dataset_id=dataset_id))
        self.assertRedirects(resp, url_for("user.profile", musicbrainz_id=self.test_user_mb_name))
        self.assertTrue(len(dataset.get_by_user_id(self.test_user_id)) == 0)

    def test_recording_info(self):
        recording_mbid = "770cc467-8dde-4d22-bc4c-a42f91e7515e"

        resp = self.client.get(url_for("datasets.recording_info", mbid=recording_mbid))
        self.assertStatus(resp, 302)
        resp = self.client.get(url_for("datasets.recording_info", mbid=self.test_uuid))
        self.assertStatus(resp, 302)

        # With logged in user
        self.temporary_login(self.test_user_id)

        resp = self.client.get(url_for("datasets.recording_info", mbid=recording_mbid))
        self.assert200(resp)
        resp = self.client.get(url_for("datasets.recording_info", mbid=self.test_uuid))
        self.assert404(resp)

class DatasetsListTestCase(ServerTestCase):

    def setUp(self):
        self.ds = {"id": "id", "author_name": "author", "name": "name",
                "created": datetime.datetime.now(), "status": "done"}

    @mock.patch("db.dataset.get_public_datasets")
    def test_page(self, get_public_datasets):
        # No page number, invalid page number
        # page number more than num pages in data
        get_public_datasets.return_value = [self.ds]

        resp = self.client.get(url_for("datasets.list_datasets", status="all"))
        get_public_datasets.assert_called_once_with("all")
        self.assertEqual(1, self.get_context_variable("page"))

        # A page which is more than the number of pages gets cut back
        url = url_for("datasets.list_datasets", status="all")
        resp = self.client.get("%s?page=4" % url)
        self.assertEqual(1, self.get_context_variable("page"))

        # A non-number gets changed to 1
        url = url_for("datasets.list_datasets", status="all")
        resp = self.client.get("%s?page=apage" % url)
        self.assertEqual(1, self.get_context_variable("page"))

    @mock.patch("db.dataset.get_public_datasets")
    def test_page_links(self, get_public_datasets):
        # If we're on the first page, show no link back
        get_public_datasets.return_value = [self.ds] * 12
        resp = self.client.get(url_for("datasets.list_datasets", status="all"))
        get_public_datasets.assert_called_once_with("all")
        self.assertEqual(None, self.get_context_variable("prevpage"))
        self.assertEqual("/datasets/list?page=2", self.get_context_variable("nextpage"))

        # if we're on the last page, show no forward link
        url = url_for("datasets.list_datasets", status="all")
        resp = self.client.get("%s?page=2" % url)
        self.assertEqual("/datasets/list?page=1", self.get_context_variable("prevpage"))
        self.assertEqual(None, self.get_context_variable("nextpage"))

    @mock.patch("db.dataset.get_public_datasets")
    def test_status(self, get_public_datasets):
        # no status, other status causes mock to change, invalid value is changed to all
        get_public_datasets.return_value = [self.ds]

        resp = self.client.get(url_for("datasets.list_datasets", status="all"))
        get_public_datasets.assert_called_once_with("all")
        get_public_datasets.reset_mock()

        resp = self.client.get(url_for("datasets.list_datasets", status="pending"))
        get_public_datasets.assert_called_once_with("pending")
        get_public_datasets.reset_mock()

        resp = self.client.get(url_for("datasets.list_datasets", status="running"))
        get_public_datasets.assert_called_once_with("running")
        get_public_datasets.reset_mock()

        resp = self.client.get(url_for("datasets.list_datasets", status="done"))
        get_public_datasets.assert_called_once_with("done")
        get_public_datasets.reset_mock()

        resp = self.client.get(url_for("datasets.list_datasets", status="failed"))
        get_public_datasets.assert_called_once_with("failed")
        get_public_datasets.reset_mock()

        resp = self.client.get(url_for("datasets.list_datasets", status="notastatus"))
        get_public_datasets.assert_called_once_with("all")
        get_public_datasets.reset_mock()
