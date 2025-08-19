# 0006 XLS-6d Standard for Visual Account Icons

Following from XLS-5d ( https://github.com/xrp-community/standards-drafts/issues/6 ) it has become necessary to provide XRPL users a way to identify their XRPL account, which effectively now has two different identifiers: an 'r-address' and an 'X-address'.

To solve this problem XLS-6d provides for a standard way to visually identify accounts irrespective of which addressing system is used by the rest of the user interface.

For a user account take the X-address of the account without destination tag and feed it into hashicon https://www.npmjs.com/package/hashicon

For an exchange, take the X-address of the account with the destination tag and feed it into hashicon.

It's recommended that these icons are displayed alongside addresses to help reduce user confusion. See examples in Figures 1 and 2.

![image](https://user-images.githubusercontent.com/19866478/65387069-ba273a80-dd86-11e9-8680-34488e15401d.png)
Figure 1

![image](https://user-images.githubusercontent.com/19866478/65387078-dc20bd00-dd86-11e9-90af-126edf511060.png)
Figure 2